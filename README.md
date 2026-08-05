# 🛡️ Aegis AI | Enterprise Code Command Center & Automated Reviewer

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Celery](https://img.shields.io/badge/Celery-Background%20Workers-green.svg)](https://docs.celeryq.dev/)

**Aegis AI** is a production-grade, event-driven DevSecOps platform designed to automate pull request code reviews, detect security vulnerabilities (like SQL injections and resource leaks), and provide engineering managers with real-time velocity metrics. 

Unlike basic API scripts, Aegis AI is built with an enterprise architecture featuring asynchronous task queues, cryptographic webhook verification, and stateful agentic AI workflows.

---

## 🏛️ System Architecture

```text
[ GitHub PR / Webhook ] 
         │ (HMAC SHA-256 Verified)
         ▼
[ FastAPI Gateway ] ──(Offloads via Celery)──> [ Redis Broker ]
         │                                            │
         ▼                                            ▼
[ Streamlit UI Dashboard ] <──[ Supabase DB ]<── [ Celery Worker Node ]
                                                      │
                                                      ▼
                                           [ LangGraph + Gemini AI ]

✨ Key Features
🧠 Agentic State Graph: Built using LangGraph to process code diffs deterministically and return structured Markdown feedback.

⚡ Asynchronous Scaling: Decouples GitHub webhooks using Celery + Redis to prevent request timeouts under high enterprise concurrency.

🔒 Cryptographic Security: Enforces strict HMAC SHA-256 signature verification (X-Hub-Signature-256) to block webhook spoofing.

📊 Executive Analytics UI: Features a polished Streamlit dashboard (Aegis AI) complete with KPI metrics, repository filtering, and an interactive code-review sandbox.

💾 Persistent Telemetry: Automatically logs review outcomes and security telemetry to a Supabase (PostgreSQL) database.

🛠️ Tech Stack
Backend: FastAPI, Uvicorn, Celery, Redis, Python-Dotenv

AI & Orchestration: LangGraph, LangChain, Google Gemini API (gemini-3.5-flash-lite)

Database & Storage: Supabase (PostgreSQL)

Frontend: Streamlit, Pandas

Security & DevOps: GitHub Webhooks, HMAC, Git, Render

🚀 Step-by-Step Installation & Local Setup Guide
Follow these instructions to run the entire enterprise stack locally on your machine or GitHub Codespace.

Prerequisites
Python 3.12+ installed

Redis Server installed locally

A Google Gemini API Key

A Supabase project (with a reviews table)

Step 1: Clone the Repository
Bash
git clone [https://github.com/parasbishnoi029/ai-reviewer.git](https://github.com/parasbishnoi029/ai-reviewer.git)
cd ai-reviewer
Step 2: Install Dependencies
Install all required Python packages:

Bash
pip install -r requirements.txt
Step 3: Configure Environment Variables
Create a .env file in the root directory of the project and populate your keys:

Code snippet
GOOGLE_API_KEY=your_gemini_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret_here
REDIS_URL=redis://localhost:6379/0
Step 4: Start Redis Server
Celery requires Redis as a message broker. Start your local Redis daemon:

Bash
redis-server --daemonize yes
Step 5: Run the Services
You need to run both the FastAPI web server and the Celery background worker concurrently. Open your terminal and run:

Terminal Window 1 (FastAPI & Celery Worker):

Bash
uvicorn main:app --host 0.0.0.0 --port 10000 & celery -A tasks worker --loglevel=info
Terminal Window 2 (Streamlit Dashboard):
Open a separate terminal tab and launch the dashboard UI:

Bash
streamlit run dashboard.py
🧪 How to Test Your Setup
Test the Live Assistant: Open the Streamlit link provided in your terminal (usually http://localhost:8501), navigate to the Live Code Assistant tab, paste any snippet of code, and click 🚀 Analyze Code.

Test GitHub Integration: Open a Pull Request in your repository with a code change. The GitHub webhook will hit your FastAPI backend, queue the task securely via Celery, process it through LangGraph, and automatically post an AI code review comment directly onto your Pull Request!

📄 License
This project is open-source and available under the MIT License.
