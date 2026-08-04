from fastapi import FastAPI, Request
import httpx
import os
from dotenv import load_dotenv
from graph import ai_reviewer_graph

load_dotenv()
app = FastAPI()

# The token we just saved
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
        comments_url = pr_data["comments_url"] # Where we send the AI feedback
        
        async with httpx.AsyncClient() as client:
            # 1. Fetch the diff
            diff_response = await client.get(diff_url)
            if diff_response.status_code == 200:
                code_diff = diff_response.text
                
                # 2. Get AI Feedback
                result = ai_reviewer_graph.invoke({"code_diff": code_diff})
                ai_feedback = result["feedback"]
                
                # 3. Post the comment back to GitHub!
                headers = {
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json"
                }
                comment_payload = {"body": f"🤖 **AI Code Review:**\n\n{ai_feedback}"}
                
                await client.post(comments_url, headers=headers, json=comment_payload)
                print("✅ Successfully posted AI review to GitHub!")
                
    return {"status": "success"}
