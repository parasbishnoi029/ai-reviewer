from fastapi import FastAPI, Request
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from graph import ai_reviewer_graph

load_dotenv()
app = FastAPI()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

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
                
                headers = {
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                }
                comment_payload = {"body": f"🤖 **AI Code Review:**\n\n{ai_feedback}"}
                
                # Post to GitHub
                await client.post(comments_url, headers=headers, json=comment_payload)
                print("✅ Successfully posted AI review to GitHub!")
                
                # --- NEW: SAVE TO DATABASE FOR DASHBOARD ---
                review_record = {
                    "pr_url": pr_html_url,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "feedback": ai_feedback
                }
                
                # Load existing reviews or start fresh
                reviews = []
                if os.path.exists("reviews.json"):
                    with open("reviews.json", "r") as f:
                        reviews = json.load(f)
                        
                reviews.append(review_record)
                
                # Save back to file
                with open("reviews.json", "w") as f:
                    json.dump(reviews, f, indent=4)
                print("✅ Saved review to local database!")
                
    return {"status": "success"}
