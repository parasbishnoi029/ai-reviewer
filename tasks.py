import logging
import os 
from datetime import datetime, timezone
from typing import Optional

import requests
from celery import Celery
from dotenv import load_dotenv
from supabase import create_client

from graph import ai_reviewer_graph


# ============================================================
# ENVIRONMENT + LOGGING
# ============================================================

load_dotenv()

logging.basicConfig(
    level=os.environ.get(
        "LOG_LEVEL",
        "INFO",
    )
)

logger = logging.getLogger(
    "aegis.worker"
)


# ============================================================
# CELERY / REDIS
# ============================================================

REDIS_URL = os.environ.get(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

celery_app = Celery(
    "reviewer_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(

    # Only accept JSON-serialized tasks/results.
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Better visibility for long AI jobs.
    task_track_started=True,

    # Prevent a stuck LLM/API call from occupying
    # a worker forever.
    task_soft_time_limit=270,
    task_time_limit=300,

    # AI jobs can be expensive/slow.
    # Do not let one worker reserve many tasks.
    worker_prefetch_multiplier=1,
)


# ============================================================
# SUPABASE
# ============================================================

SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "",
).strip()

SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "",
).strip()


if (
    SUPABASE_URL
    and SUPABASE_KEY
):

    supabase = create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )

else:

    supabase = None

    logger.warning(
        "Supabase is not configured. "
        "Reviews will still run, but analytics "
        "will not be persisted."
    )


# ============================================================
# GITHUB CONFIGURATION
# ============================================================

GITHUB_TOKEN = os.environ.get(
    "GITHUB_TOKEN",
    "",
).strip()


# Retry only errors that can realistically recover.
#
# We do NOT retry normal 401 / 403 / 404 responses.

RETRYABLE_STATUS_CODES = {
    408,  # Request Timeout
    425,  # Too Early
    429,  # Rate Limited
    500,
    502,
    503,
    504,
}


MAX_DIFF_BYTES = int(
    os.environ.get(
        "MAX_DIFF_BYTES",
        500 * 1024,
    )
)


# ============================================================
# CUSTOM RETRYABLE ERROR
# ============================================================

class RetryableGitHubError(
    requests.RequestException
):
    """GitHub error that may succeed when retried."""


# ============================================================
# GITHUB HEADERS
# ============================================================

def _github_headers() -> dict:

    headers = {
        "Accept": (
            "application/vnd.github+json"
        ),
        "User-Agent": (
            "Aegis-AI-Code-Reviewer"
        ),
        "X-GitHub-Api-Version": (
            "2022-11-28"
        ),
    }

    if GITHUB_TOKEN:

        headers[
            "Authorization"
        ] = (
            f"Bearer {GITHUB_TOKEN}"
        )

    return headers


# ============================================================
# GITHUB HTTP STATUS HANDLING
# ============================================================

def _raise_for_github(
    response: requests.Response,
) -> None:

    if (
        response.status_code
        in RETRYABLE_STATUS_CODES
    ):

        raise RetryableGitHubError(
            (
                "Retryable GitHub status: "
                f"{response.status_code}"
            ),
            response=response,
        )

    # This raises normally for other 4xx / 5xx errors.
    #
    # Important:
    # 401 / 403 / 404 are NOT automatically retried.

    response.raise_for_status()


# ============================================================
# SUPABASE PERSISTENCE
# ============================================================

def _persist_review(
    record: dict,
) -> None:

    if not supabase:
        return

    try:

        supabase.table(
            "reviews"
        ).insert(
            record
        ).execute()

    except Exception:

        # Analytics persistence should not cause a completed
        # GitHub review to fail.

        logger.exception(
            "Failed to persist "
            "review analytics."
        )


# ============================================================
# POST REVIEW TO GITHUB
# ============================================================

def _post_github_comment(
    comments_url: str,
    feedback: str,
) -> None:

    if not GITHUB_TOKEN:

        logger.warning(
            "GITHUB_TOKEN is missing. "
            "Review generated but not posted "
            "to GitHub."
        )

        return

    if not comments_url:

        logger.warning(
            "No GitHub comments URL was provided."
        )

        return

    response = requests.post(
        comments_url,
        json={
            "body": feedback
        },
        headers=_github_headers(),
        timeout=(
            5,
            20,
        ),
    )

    _raise_for_github(
        response
    )


# ============================================================
# CELERY PR REVIEW TASK
# ============================================================

@celery_app.task(
    bind=True,

    # Maximum retry attempts.
    max_retries=3,

    # Exponential retry delay.
    retry_backoff=True,

    # Prevent extremely long retry delays.
    retry_backoff_max=120,

    # Add jitter so multiple workers do not retry
    # at exactly the same moment.
    retry_jitter=True,
)
def process_pr_review(
    self,

    pr_number: int,
    repo_name: str,
    diff_url: str,
    comments_url: str,

    delivery_id: Optional[str] = None,
    commit_sha: Optional[str] = None,
):

    started_at = datetime.now(
        timezone.utc
    )

    logger.info(
        "Starting review: %s PR #%s",
        repo_name,
        pr_number,
    )

    try:

        # ====================================================
        # 1. DOWNLOAD PR DIFF
        # ====================================================

        diff_response = requests.get(
            diff_url,
            headers=_github_headers(),
            timeout=(
                5,
                20,
            ),
        )

        _raise_for_github(
            diff_response
        )

        code_diff = (
            diff_response.text
        )


        # ====================================================
        # 2. DIFF SIZE PROTECTION
        # ====================================================

        diff_size = len(
            code_diff.encode(
                "utf-8"
            )
        )

        if (
            diff_size
            > MAX_DIFF_BYTES
        ):

            logger.warning(
                (
                    "PR #%s diff is too large "
                    "(%s bytes)."
                ),
                pr_number,
                diff_size,
            )

            feedback = """
## 🛡️ Aegis AI Code Review

### ⚠️ Automated Review Skipped

This pull-request diff exceeds the configured
automated review size limit.

Large diffs reduce review quality and can exceed
AI context or processing limits.

Consider:

- splitting the change into smaller pull requests
- reviewing critical files separately
- using the Live Code Review for targeted analysis
"""

            result = {
                "overall_score": None,
                "risk_level": (
                    "Not Scored"
                ),
                "issue_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            }

        else:

            # =================================================
            # 3. RUN AEGIS AI REVIEW GRAPH
            # =================================================

            result = (
                ai_reviewer_graph.invoke(
                    {
                        "code_diff": (
                            code_diff
                        )
                    }
                )
            )

            feedback = result.get(
                "feedback",
                (
                    "Aegis AI completed the review "
                    "but no report was generated."
                ),
            )


        # ====================================================
        # 4. POST RESULT TO GITHUB
        # ====================================================

        _post_github_comment(
            comments_url,
            feedback,
        )


        # ====================================================
        # 5. CALCULATE REVIEW LATENCY
        # ====================================================

        completed_at = datetime.now(
            timezone.utc
        )

        duration_ms = int(
            (
                completed_at
                - started_at
            ).total_seconds()
            * 1000
        )


        # ====================================================
        # 6. STRUCTURED ANALYTICS RECORD
        # ====================================================

        record = {

            "pr_number": (
                pr_number
            ),

            "repo_name": (
                repo_name
            ),

            "review_comment": (
                feedback
            ),

            "overall_score": (
                result.get(
                    "overall_score"
                )
            ),

            "risk_level": (
                result.get(
                    "risk_level"
                )
            ),

            "issue_count": (
                result.get(
                    "issue_count",
                    0,
                )
            ),

            "critical_count": (
                result.get(
                    "critical_count",
                    0,
                )
            ),

            "high_count": (
                result.get(
                    "high_count",
                    0,
                )
            ),

            "medium_count": (
                result.get(
                    "medium_count",
                    0,
                )
            ),

            "low_count": (
                result.get(
                    "low_count",
                    0,
                )
            ),

            "delivery_id": (
                delivery_id
            ),

            "commit_sha": (
                commit_sha
            ),

            "review_duration_ms": (
                duration_ms
            ),

            "created_at": (
                completed_at.isoformat()
            ),
        }


        # ====================================================
        # 7. SAVE ANALYTICS
        # ====================================================

        _persist_review(
            record
        )


        # ====================================================
        # 8. LOG COMPLETION
        # ====================================================

        logger.info(
            (
                "Completed review: %s PR #%s "
                "| score=%s risk=%s "
                "| findings=%s | %sms"
            ),
            repo_name,
            pr_number,
            result.get(
                "overall_score"
            ),
            result.get(
                "risk_level"
            ),
            result.get(
                "issue_count",
                0,
            ),
            duration_ms,
        )


        # ====================================================
        # 9. CELERY RESULT
        # ====================================================

        return {

            "status": (
                "review_complete"
            ),

            "repository": (
                repo_name
            ),

            "pr_number": (
                pr_number
            ),

            "score": (
                result.get(
                    "overall_score"
                )
            ),

            "risk_level": (
                result.get(
                    "risk_level"
                )
            ),

            "issue_count": (
                result.get(
                    "issue_count",
                    0,
                )
            ),

            "duration_ms": (
                duration_ms
            ),
        }


    # ========================================================
    # RETRYABLE GITHUB STATUS
    # ========================================================

    except RetryableGitHubError as exc:

        logger.warning(
            (
                "Retryable GitHub error "
                "for %s PR #%s: %s"
            ),
            repo_name,
            pr_number,
            exc,
        )

        raise self.retry(
            exc=exc
        )


    # ========================================================
    # NETWORK FAILURE
    # ========================================================

    except (
        requests.Timeout,
        requests.ConnectionError,
    ) as exc:

        logger.warning(
            (
                "Temporary network error "
                "for %s PR #%s: %s"
            ),
            repo_name,
            pr_number,
            exc,
        )

        raise self.retry(
            exc=exc
        )


    # ========================================================
    # NON-RETRYABLE GITHUB HTTP FAILURE
    # ========================================================

    except requests.HTTPError as exc:

        status_code = None

        if (
            exc.response
            is not None
        ):

            status_code = (
                exc.response.status_code
            )

        logger.exception(
            (
                "Non-retryable GitHub "
                "HTTP error for %s PR #%s "
                "(status=%s)."
            ),
            repo_name,
            pr_number,
            status_code,
        )

        raise


    # ========================================================
    # APPLICATION / AI FAILURE
    # ========================================================

    except Exception:

        # Do not blindly retry every application error.
        #
        # Schema errors, programming bugs, invalid AI output,
        # etc. are unlikely to become correct just because the
        # same task runs again.

        logger.exception(
            (
                "Aegis review failed "
                "for %s PR #%s."
            ),
            repo_name,
            pr_number,
        )

        raise
