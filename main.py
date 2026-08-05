import hashlib 
import hmac
import logging 
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    status,
)
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from graph import ai_reviewer_graph
from tasks import process_pr_review


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

logging.basicConfig(
    level=os.environ.get(
        "LOG_LEVEL",
        "INFO",
    )
)

logger = logging.getLogger(
    "aegis.api"
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Aegis AI Code Reviewer API",
    version="2.0.0",
    description=(
        "AI-assisted code review and "
        "GitHub pull-request review API."
    ),
)


# ============================================================
# SECURITY CONFIGURATION
# ============================================================

WEBHOOK_SECRET = os.environ.get(
    "GITHUB_WEBHOOK_SECRET",
    "",
).strip()

API_KEY = os.environ.get(
    "API_KEY",
    "",
).strip()


# Never silently fall back to something like:
#
# API_KEY = "dev-secret-key"
#
# That makes authentication look enabled while using a
# predictable credential.

if not API_KEY:
    raise RuntimeError(
        "API_KEY is required. "
        "Refusing to start with a default credential."
    )


if not WEBHOOK_SECRET:
    logger.warning(
        "GITHUB_WEBHOOK_SECRET is not configured. "
        "/webhook will reject requests until it is set."
    )


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


# ============================================================
# API KEY AUTHENTICATION
# ============================================================

def verify_api_key(
    api_key: Optional[str] = Depends(
        api_key_header
    ),
) -> str:

    if not api_key:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Missing API key.",
        )

    # Constant-time comparison avoids normal string
    # comparison for authentication secrets.

    if not hmac.compare_digest(
        api_key,
        API_KEY,
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Invalid API key.",
        )

    return api_key


# ============================================================
# GITHUB WEBHOOK SIGNATURE VERIFICATION
# ============================================================

async def verify_github_signature(
    request: Request,
    signature_header: Optional[str],
) -> None:

    if not WEBHOOK_SECRET:

        # Fail closed.
        #
        # We do NOT silently accept unsigned webhooks when
        # the environment variable is missing.

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Webhook verification "
                "is not configured."
            ),
        )

    if not signature_header:

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Missing X-Hub-Signature-256 header."
            ),
        )

    payload_body = await request.body()

    # Prevent unexpectedly large webhook bodies.
    #
    # GitHub PR diffs are retrieved separately by the worker,
    # so the webhook itself should not need a huge payload.

    max_webhook_size = (
        5 * 1024 * 1024
    )

    if len(payload_body) > max_webhook_size:

        raise HTTPException(
            status_code=(
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            ),
            detail="Webhook payload too large.",
        )

    digest = hmac.new(
        WEBHOOK_SECRET.encode(
            "utf-8"
        ),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    expected_signature = (
        f"sha256={digest}"
    )

    if not hmac.compare_digest(
        signature_header,
        expected_signature,
    ):

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail="Invalid webhook signature.",
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    tags=["System"],
)
async def health():

    return {
        "status": "ok",
        "service": "aegis-api",
        "version": "2.0.0",
    }


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get(
    "/",
    tags=["System"],
)
async def root():

    return {
        "service": "Aegis AI",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# GITHUB WEBHOOK
# ============================================================

@app.post(
    "/webhook",
    status_code=(
        status.HTTP_202_ACCEPTED
    ),
    tags=["GitHub"],
)
async def github_webhook(
    request: Request,

    x_hub_signature_256: Optional[str] = Header(
        default=None
    ),

    x_github_delivery: Optional[str] = Header(
        default=None
    ),
):

    # --------------------------------------------------------
    # Verify GitHub signature BEFORE trusting JSON payload.
    # --------------------------------------------------------

    await verify_github_signature(
        request,
        x_hub_signature_256,
    )

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        payload = await request.json()

    except Exception as exc:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail="Invalid JSON payload.",
        ) from exc

    # --------------------------------------------------------
    # Validate event
    # --------------------------------------------------------

    action = payload.get(
        "action"
    )

    if (
        "pull_request" not in payload
        or action not in {
            "opened",
            "synchronize",
        }
    ):

        return {
            "status": "ignored",
            "message": (
                "Event is not reviewable."
            ),
        }

    # --------------------------------------------------------
    # Extract required PR information
    # --------------------------------------------------------

    try:

        pr = payload[
            "pull_request"
        ]

        repository = payload[
            "repository"
        ]

        pr_number = int(
            pr["number"]
        )

        repo_name = repository[
            "full_name"
        ]

        diff_url = pr[
            "diff_url"
        ]

        comments_url = pr[
            "comments_url"
        ]

        commit_sha = (
            pr.get(
                "head",
                {},
            ).get(
                "sha"
            )
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:

        logger.warning(
            "Malformed GitHub PR payload: %s",
            exc,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Malformed pull-request payload."
            ),
        ) from exc

    # --------------------------------------------------------
    # Queue Celery job
    # --------------------------------------------------------

    try:

        process_pr_review.delay(
            pr_number=pr_number,
            repo_name=repo_name,
            diff_url=diff_url,
            comments_url=comments_url,
            delivery_id=(
                x_github_delivery
            ),
            commit_sha=(
                commit_sha
            ),
        )

    except Exception:

        logger.exception(
            "Failed to queue review "
            "for %s PR #%s.",
            repo_name,
            pr_number,
        )

        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Review queue is unavailable."
            ),
        )

    return {
        "status": "queued",
        "message": (
            "PR review queued successfully."
        ),
        "repository": repo_name,
        "pr_number": pr_number,
    }


# ============================================================
# MANUAL REVIEW PAYLOAD
# ============================================================

class ManualReviewPayload(
    BaseModel
):

    code: str = Field(
        min_length=1,
        max_length=(
            100 * 1024
        ),
        description=(
            "Standalone source code or "
            "code diff to review."
        ),
    )


# ============================================================
# MANUAL REVIEW ENDPOINT
# ============================================================

@app.post(
    "/manual-review",
    tags=["Review"],
)
async def manual_review(
    payload: ManualReviewPayload,

    _: str = Depends(
        verify_api_key
    ),
):

    try:

        result = (
            ai_reviewer_graph.invoke(
                {
                    "code_diff": (
                        payload.code
                    )
                }
            )
        )

        return {

            # Human-readable Markdown report

            "feedback": result.get(
                "feedback",
                "No response generated.",
            ),

            # Structured telemetry

            "score": result.get(
                "overall_score"
            ),

            "risk_level": result.get(
                "risk_level"
            ),

            "issue_count": result.get(
                "issue_count",
                0,
            ),

            "counts": {

                "critical": result.get(
                    "critical_count",
                    0,
                ),

                "high": result.get(
                    "high_count",
                    0,
                ),

                "medium": result.get(
                    "medium_count",
                    0,
                ),

                "low": result.get(
                    "low_count",
                    0,
                ),
            },
        }

    except Exception:

        # Log the real exception internally.
        #
        # Do NOT return exception details to the client because
        # they may expose implementation details or credentials.

        logger.exception(
            "Manual review failed."
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Code review failed.",
        )
