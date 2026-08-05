import os
import requests
from celery import Celery
from supabase import create_client, Client
from graph import ai_reviewer_graph
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("reviewer_tasks", broker=REDIS_URL)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Add Celery retry/error handling for network failures
@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_pr_review(self, pr_number: int, repo_name: str, diff_url: str, comments_url: str):
    """Fetches diff, executes LangGraph AI, and pushes results."""
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        
        # 1. Move diff fetching into Celery with HTTP Timeouts
        diff_response = requests.get(diff_url, headers=headers, timeout=10)
        diff_response.raise_for_status() # Crash and trigger retry if 4xx/5xx
        code_diff = diff_response.text
        
        # 2. Add size limits (Skip massive PRs to save LLM tokens context window)
        if len(code_diff) > 500 * 1024: # 500 KB limit
            feedback = "⚠️ **Aegis AI:** This PR diff exceeds the automated review size limit. Please review manually."
        else:
            # 3. Run the AI Review
            result = ai_reviewer_graph.invoke({"code_diff": code_diff})
            feedback = result.get("feedback", "Review failed to generate.")
        
        # 4. Post Comment to GitHub with timeout
        if GITHUB_TOKEN and comments_url:
            github_payload = {"body": f"### 🛡️ Enterprise AI Review\n\n{feedback}"}
            comment_resp = requests.post(comments_url, json=github_payload, headers=headers, timeout=10)
            comment_resp.raise_for_status()
            
        # 5. Save to Supabase
        if supabase:
            supabase.table("reviews").insert({
                "pr_number": pr_number,
                "repo_name": repo_name,
                "review_comment": feedback
            }).execute()
            
        return {"status": "Review Complete", "pr_number": pr_number}
        
    except requests.exceptions.RequestException as exc:
        # Retry up to 3 times on network/GitHub API failures
        raise self.retry(exc=exc)
    except Exception as e:
        print(f"Failed processing PR #{pr_number}: {e}")
        raise # Let it fail into Celery's dead letter queue
