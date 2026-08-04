from fastapi import FastAPI, Request
import httpx
from graph import ai_reviewer_graph

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Hello! The AI Reviewer Server is running."}

@app.post("/webhook")
async def github_webhook(request: Request):
    # Parse the incoming JSON payload from GitHub
    payload = await request.json()
    event_action = payload.get("action")
    
    print(f"\n=== NEW WEBHOOK EVENT ===")
    print(f"Action: {event_action}")
    
    # We only care if the payload contains Pull Request data
    if "pull_request" in payload:
        diff_url = payload["pull_request"]["diff_url"]
        print(f"Fetching diff from: {diff_url}")
        
        # Download the raw code changes using httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(diff_url)
            
            if response.status_code == 200:
                code_diff = response.text
                print("Diff fetched successfully! Sending to AI...")
                
                # --- PASS THE DATA TO LANGGRAPH ---
                # This triggers the graph.py logic and waits for the LLM
                result = ai_reviewer_graph.invoke({"code_diff": code_diff})
                
                print("\n=== AI REVIEW FEEDBACK ===")
                print(result["feedback"])
                print("==========================\n")
                
            else:
                print(f"Failed to fetch diff. Status: {response.status_code}")
                
    return {"status": "success"}