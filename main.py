import os
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.security import APIKeyHeader
from tasks import process_pr_review
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Aegis AI Code Reviewer API")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
API_KEY = os.environ.get("API_KEY", "dev-secret-key") # Change this in production!

# Make missing GITHUB_WEBHOOK_SECRET fatal in production
if ENVIRONMENT == "production" and not WEBHOOK_SECRET:
    raise RuntimeError("CRITICAL: GITHUB_WEBHOOK_SECRET is missing in production environment.")

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Depends(api_key_header)):
    """Protect internal endpoints from public access."""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

async def verify_github_signature(request: Request, signature_header: str):
    if not WEBHOOK_SECRET:
        print("WARNING: Skipping signature validation (not in production).")
        return
        
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")
    
    payload_body = await request.body()
    
    # Add request size limit (e.g., 5MB) to prevent memory exhaustion attacks
    if len(payload_body) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Payload too large")

    expected_hash = hmac.new(WEBHOOK_SECRET.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature_header, f"sha256={expected_hash}"):
        raise HTTPException(status_code=403, detail="Signature mismatch! Unauthorized payload.")

@app.post("/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    await verify_github_signature(request, x_hub_signature_256)
    
    payload = await request.json()
    action = payload.get("action")
    
    if "pull_request" in payload and action in ["opened", "synchronize"]:
        pr = payload["pull_request"]
        
        # We NO LONGER fetch the diff here. We pass the URL to Celery.
        process_pr_review.delay(
            pr_number=pr["number"], 
            repo_name=payload["repository"]["full_name"], 
            diff_url=pr["diff_url"], 
            comments_url=pr["comments_url"]
        )
        return {"status": "success", "message": "PR review queued successfully."}
            
    return {"status": "ignored", "message": "Event type not supported or ignored."}

class ManualReviewPayload(BaseModel):
    code: str

# Protect this endpoint with the API Key dependency
@app.post("/manual-review")
async def manual_review(payload: ManualReviewPayload, api_key: str = Depends(verify_api_key)):
    # Add diff size limits (100KB limit for manual review)
    if len(payload.code) > 100 * 1024:
        raise HTTPException(status_code=413, detail="Code snippet exceeds 100KB limit.")
        
    from graph import ai_reviewer_graph
    try:
        result = ai_reviewer_graph.invoke({"code_diff": payload.code})
        return {"feedback": result.get("feedback", "No review generated.")}
    except Exception as e:
        return {"feedback": f"Error generating review: {str(e)}"}
