import os
import requests
from celery import Celery
from supabase import create_client, Client
from graph import ai_reviewer_graph
from dotenv import load_dotenv

load_dotenv()

# Initialize Celery with Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("reviewer_tasks", broker=REDIS_URL)

# Initialize Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

@celery_app.task
def process_pr_review(pr_number: int, repo_name: str, code_diff: str, comments_url: str):
    """Executes the LangGraph AI and pushes results to GitHub and Supabase."""
    
    # 1. Run the AI Review
    result = ai_reviewer_graph.invoke({"code_diff": code_diff})
    feedback = result.get("feedback", "Review failed to generate.")
    
    # 2. Post Comment to GitHub
    if GITHUB_TOKEN and comments_url:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        github_payload = {"body": f"### 🤖 Enterprise AI Review\n\n{feedback}"}
        requests.post(comments_url, json=github_payload, headers=headers)
        
    # 3. Save to Supabase for the Dashboard
    if supabase:
        supabase.table("reviews").insert({
            "pr_number": pr_number,
            "repo_name": repo_name,
            "review_comment": feedback
        }).execute()
        
    return {"status": "Review Complete", "pr_number": pr_number}
