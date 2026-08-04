from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Hello! The AI Reviewer Server is running."}

@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    event_action = payload.get("action")
    
    print(f"\n=== NEW WEBHOOK EVENT ===")
    print(f"Action: {event_action}")
    
    # Check if the event is a Pull Request
    if "pull_request" in payload:
        diff_url = payload["pull_request"]["diff_url"]
        print(f"Fetching diff from: {diff_url}")
        
        # Download the actual code changes
        async with httpx.AsyncClient() as client:
            response = await client.get(diff_url)
            
            if response.status_code == 200:
                code_diff = response.text
                print("\n--- ACTUAL CODE CHANGES ---")
                print(code_diff)
                print("---------------------------\n")
            else:
                print(f"Failed to fetch diff. Status: {response.status_code}")
            
    return {"status": "success"}
