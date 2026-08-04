from fastapi import FastAPI, Request

app = FastAPI()

# Add this new GET endpoint!
@app.get("/")
async def home():
    return {"message": "Hello! The AI Reviewer Server is running."}

@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    event_action = payload.get("action")
    
    print(f"Received an event! Action: {event_action}")
    
    if "pull_request" in payload:
        pr_url = payload["pull_request"]["html_url"]
        print(f"Someone opened or updated a PR at: {pr_url}")
        
    return {"status": "success"}