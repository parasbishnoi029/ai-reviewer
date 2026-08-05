# 🛡️ Aegis AI

### AI-Powered DevSecOps Code Review & Pull Request Intelligence

Aegis AI is an AI-powered code review platform designed to analyze source code and GitHub pull requests for **security vulnerabilities, performance issues, reliability problems, and code-quality concerns**.

It combines **Gemini, LangGraph, FastAPI, Celery, Redis, Supabase, and Streamlit** to provide automated code analysis through both a live code-review sandbox and an asynchronous GitHub pull-request workflow.

Instead of only identifying problems, Aegis AI explains what is already good, identifies potential issues, recommends practical fixes, and — when reviewing standalone code snippets — generates an improved version of the code.

---

## ✨ What Aegis AI Does

Aegis AI provides two main review workflows:

### 🔍 Live Code Review

Paste a standalone code snippet into the Aegis AI Command Center and receive an AI-assisted review containing:

- 🌟 **Pros** — what the code already does well
- 🚨 **Issues** — security, performance, reliability, and quality concerns
- 🛠️ **Recommended Fixes** — practical improvements for detected issues
- 💻 **Refactored Code** — an improved version of the submitted code

### 🔄 Automated GitHub PR Review

Connect Aegis AI to a GitHub repository through webhooks.

When a pull request is opened or updated, Aegis AI automatically:

1. Receives the GitHub webhook
2. Verifies the webhook signature
3. Queues the review asynchronously
4. Retrieves the pull-request diff
5. Runs the AI review workflow
6. Generates review feedback
7. Posts the review back to GitHub
8. Stores review data for analytics

---

# 🏗️ Architecture

```text
                         ┌────────────────────┐
                         │     GitHub PR      │
                         └─────────┬──────────┘
                                   │
                                   │ Webhook
                                   ▼
                         ┌────────────────────┐
                         │      FastAPI       │
                         │  Webhook Endpoint  │
                         │   HMAC Validation  │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │       Redis        │
                         │   Task Broker      │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │   Celery Worker    │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ LangGraph Workflow │
                         │      + Gemini      │
                         └─────────┬──────────┘
                                   │
                      ┌────────────┴────────────┐
                      ▼                         ▼
             ┌────────────────┐        ┌────────────────┐
             │ GitHub Review  │        │    Supabase    │
             │    Feedback    │        │ Review History │
             └────────────────┘        └───────┬────────┘
                                               │
                                               ▼
                                      ┌────────────────┐
                                      │   Streamlit    │
                                      │ Command Center │
                                      └────────────────┘
```

---

# 🧠 AI Review Workflow

The current LangGraph workflow uses specialized review stages to inspect submitted code.

```text
Input Code / Pull Request Diff
            │
            ▼
     Security Analysis
            │
            ▼
    Performance Analysis
            │
            ▼
     Refactor Analysis
            │
            ▼
      Report Formatter
            │
            ▼
       Final Review
```

The AI workflow uses structured outputs to make review results easier to validate and process programmatically.

---

# 🔍 Live Code Sandbox

The Aegis AI Command Center includes a live code-review environment.

Users can paste code directly into the dashboard and request an immediate AI-assisted review.

### Example Input

```python
import asyncio
import httpx

async def check_server(client, server):
    try:
        response = await client.get(server, timeout=5)
        return response.status_code
    except httpx.RequestError:
        return None
```

Aegis AI analyzes the code and generates a structured review.

### Example Output

```text
🛡️ Aegis AI Code Review

🌟 Pros

✅ Uses asynchronous networking
✅ Includes request timeout handling
✅ Handles network failures

🚨 Issues

[Medium] External URLs should be validated before requests
are made if input can be user-controlled.

[Low] Error handling could provide better observability.

🛠️ Recommended Fixes

🔧 Validate external URLs before making requests.

🔧 Add structured logging for failed requests.

💻 Refactored Code

[Improved implementation]
```

The goal is not only to detect problems but to explain **why they matter and how they can be improved**.

---

# 🔄 GitHub Pull Request Automation

Aegis AI can automatically review GitHub pull requests.

Supported webhook events include:

```text
pull_request.opened
pull_request.synchronize
```

When one of these events occurs:

```text
Developer opens/updates PR
          ↓
GitHub sends webhook
          ↓
Aegis verifies signature
          ↓
Review task sent to Redis
          ↓
Celery worker processes task
          ↓
PR diff retrieved
          ↓
Gemini + LangGraph analyze changes
          ↓
Review generated
          ↓
Feedback posted to GitHub
          ↓
Review stored in Supabase
```

This architecture keeps expensive AI processing outside the webhook request lifecycle.

---

# 🛡️ Security

Aegis AI includes several security controls around its API and GitHub integration.

### GitHub Webhook Verification

Incoming GitHub webhook payloads are verified using **HMAC SHA-256** signatures.

This helps ensure webhook requests originate from a trusted GitHub configuration.

### API Authentication

The manual review API uses an API key to restrict unauthorized access.

### Input Limits

Code and pull-request input sizes are restricted to prevent unexpectedly large AI requests.

### Network Timeouts

External GitHub requests use request timeouts to prevent workers from waiting indefinitely.

### Structured AI Output

AI responses are parsed through structured models instead of relying entirely on unrestricted free-form responses.

---

# ⚡ Asynchronous Processing

GitHub reviews can involve:

- GitHub API calls
- AI inference
- Database operations
- Review generation
- GitHub feedback

Running all of these operations directly inside a webhook request would make the API slow and unreliable.

Aegis therefore uses:

```text
FastAPI
   ↓
Redis
   ↓
Celery
   ↓
AI Review
```

FastAPI can acknowledge webhook requests quickly while Celery performs the heavier review process separately.

---

# 📊 Command Center

Aegis AI includes a Streamlit-based Command Center for interacting with and monitoring the system.

### Live Code Review

Submit code manually and receive:

- Pros
- Issues
- Recommended fixes
- Refactored code

### Review Analytics

Review historical activity stored in Supabase, including repository and review information.

The dashboard provides a centralized interface for both manual AI review and automated review monitoring.

---

# 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| **Python** | Core application language |
| **Gemini** | AI-powered code analysis |
| **LangGraph** | AI review workflow orchestration |
| **FastAPI** | Backend API and GitHub webhook handling |
| **Celery** | Asynchronous review processing |
| **Redis** | Celery message broker |
| **Supabase** | Review history and persistence |
| **Streamlit** | Command Center and live review interface |
| **GitHub API** | Pull-request retrieval and review feedback |
| **Pydantic** | Structured AI output and validation |
| **Pytest** | Automated testing |

---

# 📂 Project Structure

```text
ai-reviewer/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── tests/
│   └── test_main.py
│
├── main.py
├── graph.py
├── tasks.py
├── dashboard.py
├── requirements.txt
├── .env.example
├── README.md
└── LICENSE
```

### Core Files

**`main.py`**

FastAPI application responsible for:

- GitHub webhook handling
- HMAC signature verification
- Manual code-review API
- API authentication
- Request validation

**`graph.py`**

Defines the LangGraph-based AI review workflow and structured review models.

**`tasks.py`**

Contains Celery tasks responsible for:

- Retrieving GitHub PR diffs
- Running AI reviews
- Posting feedback to GitHub
- Persisting review results

**`dashboard.py`**

Streamlit Command Center providing:

- Live code review
- Review history
- Analytics

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/parasbishnoi029/ai-reviewer.git
cd ai-reviewer
```

---

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ⚙️ Environment Configuration

Create a `.env` file in the project root.

```env
GOOGLE_API_KEY=your_google_gemini_api_key

GITHUB_TOKEN=your_github_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret

API_KEY=your_dashboard_api_key

REDIS_URL=redis://localhost:6379/0

SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
```

> Never commit your real `.env` file, API keys, GitHub tokens, or database credentials.

---

# ▶️ Running Aegis AI

Aegis AI consists of multiple services.

## Start Redis

Make sure a Redis server is available.

Default configuration:

```text
redis://localhost:6379/0
```

---

## Start FastAPI

```bash
uvicorn main:app --reload
```

The backend will normally be available at:

```text
http://localhost:8000
```

FastAPI API documentation:

```text
http://localhost:8000/docs
```

---

## Start the Celery Worker

```bash
celery -A tasks.celery_app worker --loglevel=info
```

---

## Start the Command Center

```bash
streamlit run dashboard.py
```

Streamlit will normally start at:

```text
http://localhost:8501
```

---

# 🔗 GitHub Webhook Setup

Inside the GitHub repository you want Aegis AI to review:

```text
Settings
→ Webhooks
→ Add webhook
```

Configure the webhook endpoint:

```text
https://YOUR_DEPLOYED_API/github-webhook
```

Use the same secret configured as:

```env
GITHUB_WEBHOOK_SECRET=...
```

Select pull-request events.

Aegis AI can then process supported PR events automatically.

---

# 🧪 Running Tests

Run the test suite with:

```bash
pytest tests/
```

The repository also includes GitHub Actions CI so automated checks can run when code is pushed or updated.

---

# 🔐 Environment Variables

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Gemini API authentication |
| `GITHUB_TOKEN` | GitHub API authentication |
| `GITHUB_WEBHOOK_SECRET` | GitHub webhook verification |
| `API_KEY` | Manual review API authentication |
| `REDIS_URL` | Redis connection |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase authentication |

---

# 🧭 Current Capabilities

Aegis AI currently supports:

- AI-assisted code review
- Security-focused analysis
- Performance-focused analysis
- Code improvement recommendations
- Refactored code generation for standalone snippets
- GitHub pull-request webhook automation
- HMAC webhook validation
- Asynchronous review processing
- GitHub review feedback
- Review history persistence
- Streamlit review dashboard
- Structured AI responses
- Automated tests and CI

---

# 🗺️ Roadmap

Aegis AI is actively evolving toward a more context-aware and reliable AI review architecture.

### 🚧 Planned Improvements

- [ ] Parallel security, performance, quality, and testing review agents
- [ ] Repository-aware code context
- [ ] Changed-file and dependency context retrieval
- [ ] Finding confidence scores
- [ ] Finding deduplication
- [ ] Deterministic risk scoring
- [ ] PR review verdicts
- [ ] GitHub inline code suggestions
- [ ] Configurable `.aegis.yml` review policies
- [ ] Intelligent large-PR chunking
- [ ] Generated-file and lock-file filtering
- [ ] Improved prompt-injection defenses
- [ ] Expanded automated test coverage
- [ ] Ruff linting and formatting checks
- [ ] Static type checking
- [ ] Dependency and security scanning
- [ ] Docker and Docker Compose support
- [ ] Health and readiness endpoints
- [ ] Review latency and failure analytics
- [ ] AI token and cost telemetry

### Target Review Architecture

```text
                         Pull Request
                              │
                              ▼
                       Context Builder
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
          Security       Performance       Quality
           Agent            Agent           Agent
              │               │               │
              │               ▼               │
              │          Testing Agent        │
              │               │               │
              └───────────────┼───────────────┘
                              │
                              ▼
                         Aggregator
                              │
                     ┌────────┴────────┐
                     │                 │
                Deduplicate       Confidence
                     │                 │
                     └────────┬────────┘
                              │
                              ▼
                         Risk Engine
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               GitHub Review        Analytics
```

---

# 🎯 Design Philosophy

Aegis AI is built around a simple principle:

> **AI should assist engineering judgment, not replace it.**

The system aims to combine AI reasoning with deterministic software controls.

AI is useful for:

- Understanding code
- Identifying potential problems
- Explaining risks
- Suggesting improvements
- Generating refactoring ideas

Traditional software logic remains important for:

- Authentication
- Validation
- Rate and size limits
- Severity policies
- Confidence thresholds
- Workflow control
- Data persistence
- Error handling

This separation helps make AI-assisted development tools more predictable and useful.

---

# ⚠️ Limitations

Aegis AI uses large language models, and AI-generated code reviews can contain incorrect findings, missed issues, or unsuitable recommendations.

Aegis AI should therefore be treated as an **engineering assistant**, not as a replacement for:

- Human code review
- Static-analysis tools
- Security testing
- Dependency scanning
- Automated testing
- Professional security audits

Generated refactored code should always be reviewed and tested before being used in production.

---

# 🤝 Contributing

Contributions, bug reports, and improvement suggestions are welcome.

To contribute:

```text
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add or update tests
5. Open a pull request
```

---

# 📄 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for details.

---

# 👨‍💻 Author

**Paras**

GitHub: `@parasbishnoi029`

---

## ⭐ Support

If you find Aegis AI useful or interesting, consider giving the repository a ⭐.

It helps the project reach more developers and supports continued development.

---

**🛡️ Aegis AI — AI-assisted code review for safer, cleaner, and more maintainable software.**
