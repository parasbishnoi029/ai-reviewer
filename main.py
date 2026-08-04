from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv
from graph import ai_reviewer_graph
from supabase import create_client, Client

load_dotenv()
app = FastAPI()

# Load all 4 keys from the environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SUPABASE_URL = os.getenv(https://ylevykwrsbkjoexwznaw.supabase.co)
SUPABASE_KEY = os.getenv(sb_publishable_i0iKJaN7QDdwRp0yGg82vQ_uMAMLVT0)

# Initialize the cloud database connection
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define the data structure for our new Chatbot feature
class ManualReviewRequest(BaseModel):
    code: str

@app.get("/")
async def home():
    return {"message": "Hello! The AI Reviewer Server is running."}

@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    
    if "pull_request" in payload and payload.get("action") in ["opened", "synchronize"]:
        pr_data = payload["pull_request"]
        diff_url = pr_data["diff_url"]
        comments_url = pr_data["comments_url"]
        pr_html_url = pr_data["html_url"]
        
        async with httpx.AsyncClient() as client:
            diff_response = await client.get(diff_url)
            if diff_response.status_code == 200:
                code_diff = diff_response.text
                
                result = ai_reviewer_graph.invoke({"code_diff": code_diff})
                ai_feedback = result["feedback"]
                
                # Post the comment to GitHub
                headers = {
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                }
                comment_payload = {"body": f"🤖 **AI Code Review:**\n\n{ai_feedback}"}
                await client.post(comments_url, headers=headers, json=comment_payload)
                
                # --- NEW: SAVE TO SUPABASE INSTEAD OF LOCAL FILE ---
                record = {
                    "pr_url": pr_html_url,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "feedback": ai_feedback
                }
                supabase.table("reviews").insert(record).execute()
                print("✅ Saved review to Supabase!")
                
    return {"status": "success"}

# --- NEW: CHATBOT ENDPOINT ---
@app.post("/manual-review")
async def manual_review(req: ManualReviewRequest):
    # This directly processes code pasted into the Streamlit dashboard!
    result = ai_reviewer_graph.invoke({"code_diff": req.code})
    return {"feedback": result["feedback"]}
