import os
import hmac
import hashlib
import requests
from fastapi import FastAPI, Request, HTTPException, Header
from tasks import process_pr_review
from dotenv import load_dotenv
from pydantic import BaseModel
from graph import ai_reviewer_graph

load_dotenv()

app = FastAPI(title="Enterprise AI Code Reviewer API")

WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

async def verify_github_signature(request: Request, signature_header: str):
    """Strict HMAC SHA-256 verification for MNC-level security."""
    if not WEBHOOK_SECRET:
        # Skip verification in local dev if secret is not set, but warn
        print("WARNING: GITHUB_WEBHOOK_SECRET not set. Skipping signature validation.")
        return
        
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")
    
    payload_body = await request.body()
    expected_hash = hmac.new(WEBHOOK_SECRET.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
    expected_signature = f"sha256={expected_hash}"
    
    if not hmac.compare_digest(signature_header, expected_signature):
        raise HTTPException(status_code=403, detail="Signature mismatch! Unauthorized payload.")

class CodePayload(BaseModel):
    code: str

@app.post("/manual-review")
async def manual_review(payload: CodePayload):
    # Runs instantly (no celery) for the live chat UI
    result = ai_reviewer_graph.invoke({"code_diff": payload.code})
    return {"feedback": result.get("feedback", "")}
@app.post("/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    # 1. Enforce Security
    await verify_github_signature(request, x_hub_signature_256)
    
    payload = await request.json()
    action = payload.get("action")
    
    # 2. Process only PR openings or updates
    if "pull_request" in payload and action in ["opened", "synchronize"]:
        pr = payload["pull_request"]
        pr_number = pr["number"]
        repo_name = payload["repository"]["full_name"]
        diff_url = pr["diff_url"]
        comments_url = pr["comments_url"]
        
        # Fetch the diff from GitHub
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        diff_response = requests.get(diff_url, headers=headers)
        
        if diff_response.status_code == 200:
            code_diff = diff_response.text
            
            # Offload to Celery Queue instead of blocking the API
            process_pr_review.delay(pr_number, repo_name, code_diff, comments_url)
            
            return {"status": "success", "message": "PR review queued successfully."}
        else:
            raise HTTPException(status_code=400, detail="Failed to fetch PR diff.")
            
    return {"status": "ignored", "message": "Event type not supported or ignored."}
