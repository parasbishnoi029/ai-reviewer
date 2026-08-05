# 🛡️ Aegis AI

### AI-Powered DevSecOps Code Review & Pull Request Intelligence

Aegis AI is an AI-powered DevSecOps code review platform that analyzes source code and GitHub pull requests for **security, performance, reliability, and code-quality concerns**.

Powered by **Google Gemini and LangGraph**, Aegis AI transforms code into a structured engineering audit containing an **overall score, risk level, executive summary, validated strengths, severity-classified findings, confidence indicators, issue-linked fixes, and refactored code**.

The platform combines **FastAPI, LangGraph, Gemini, Celery, Redis, Supabase, Streamlit, and the GitHub API** to provide both interactive code analysis and automated pull-request reviews.

---

## ✨ Core Features

### 📊 Code Quality Scoring

Every review provides an overall score:

```text
Overall Score: 90 / 100
Risk Level: Low
```

The score gives developers a quick summary of the review before they inspect individual findings.

It should be interpreted together with the detailed findings rather than treated as an absolute measurement of software quality.

---

### 📝 Executive Summary

Aegis AI generates a concise summary describing:

- Overall code quality
- Important security observations
- Performance characteristics
- Main engineering concerns
- General review outcome

Example:

```text
Executive Summary:

The code follows several strong security and asynchronous
programming practices, while a small number of reliability
and performance improvements may still be appropriate.
```

---

### 🌟 Validated Pros

Aegis AI identifies engineering practices that are already implemented well.

Examples include:

- Input validation
- Secure coding patterns
- Asynchronous programming
- Error handling
- Resource management
- Clear implementation patterns

This allows the review to distinguish between code that should be preserved and code that should be changed.

---

### 🚨 Structured Findings

Detected issues are presented using structured metadata.

Example:

```text
[LOW | Performance | Confidence: High]

Location:
check_server_status

Finding:
Creating a new network client for every invocation may
prevent connection reuse across repeated calls.
```

Each finding can contain:

- **Severity**
- **Category**
- **Confidence**
- **Code location**
- **Technical explanation**

---

### 🛠️ Issue-Linked Fixes

Every recommendation is connected to the finding it addresses.

Example:

```text
🔧 Fix for check_server_status [Performance]

Consider reusing a long-lived HTTP client when the
function is called repeatedly so connections can be
reused across operations.
```

This creates a clear relationship:

```text
Problem
   ↓
Severity + Category
   ↓
Confidence
   ↓
Recommended Fix
```

---

### 💻 Refactored Code

For standalone snippets submitted through the Live Code Sandbox, Aegis AI can generate an improved implementation based on the review findings.

```text
Original Code
      ↓
AI Analysis
      ↓
Structured Findings
      ↓
Issue-Linked Fixes
      ↓
Refactored Code
```

Generated code should always be reviewed and tested before being used in production.

---

# 🔍 Live Code Sandbox

The Aegis AI Command Center provides an interactive environment for analyzing standalone code snippets.

Paste code into the editor and run an AI-assisted review.

A complete review can contain:

```text
🛡️ Aegis AI Code Audit Report

📊 Executive Telemetry

Overall Score: 90 / 100
Risk Level: Low

Executive Summary:
[High-level analysis]

🌟 Validated Pros

✅ Good engineering practice
✅ Security or performance strength

🚨 Structured Findings & Cons

[LOW | AppSec | Confidence: Medium]
Finding description...

[MEDIUM | Performance | Confidence: High]
Finding description...

🛠️ Issue-Linked Fixes

🔧 Fix for finding #1...
🔧 Fix for finding #2...

💻 Validated Refactored Code

[Improved implementation]
```

---

# 🧠 Review Structure

Aegis AI transforms raw code into a structured engineering report:

```text
                    Submitted Code
                          │
                          ▼
                  ┌───────────────┐
                  │   Aegis AI    │
                  │ Review Engine │
                  └───────┬───────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        Security Analysis      Performance Analysis
              │                       │
              └───────────┬───────────┘
                          ▼
                   Refactor Analysis
                          │
                          ▼
                    Final Report
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
  Score & Risk          Pros            Findings
                                            │
                                            ▼
                                      Linked Fixes
                                            │
                                            ▼
                                     Refactored Code
```

---

# 📋 Review Report

A complete Aegis AI review is divided into five major sections.

## 1. 📊 Executive Telemetry

Provides the high-level review result:

```text
Overall Score
Risk Level
Executive Summary
```

This allows developers to understand the general condition of the code quickly.

---

## 2. 🌟 Validated Pros

Highlights good engineering decisions already present in the implementation.

Aegis AI attempts to preserve these strengths during refactoring.

---

## 3. 🚨 Structured Findings & Cons

Potential issues are classified using:

```text
Severity
   │
   ├── Critical
   ├── High
   ├── Medium
   └── Low

Category
   │
   ├── AppSec
   ├── Performance
   └── Other supported review categories

Confidence
   │
   ├── High
   ├── Medium
   └── Low
```

This helps developers distinguish serious findings from lower-priority observations.

---

## 4. 🛠️ Issue-Linked Fixes

Recommendations are linked directly to their corresponding findings.

Instead of only reporting:

```text
"This code has a problem."
```

Aegis AI attempts to answer:

```text
What is the problem?
        ↓
Where is it?
        ↓
How serious is it?
        ↓
How confident is the review?
        ↓
Why does it matter?
        ↓
How can it be improved?
```

---

## 5. 💻 Refactored Code

For standalone code analysis, Aegis AI can produce an improved version incorporating recommended changes.

This turns the system from a simple issue detector into an AI-assisted review and remediation workflow.

---

# 🔄 Automated GitHub PR Reviews

Aegis AI can also review GitHub pull requests automatically.

Supported events include:

```text
pull_request.opened
pull_request.synchronize
```

The workflow:

```text
Developer opens / updates PR
              │
              ▼
        GitHub Webhook
              │
              ▼
      HMAC Verification
              │
              ▼
          FastAPI
              │
              ▼
            Redis
              │
              ▼
       Celery Worker
              │
              ▼
      Retrieve PR Diff
              │
              ▼
     LangGraph + Gemini
              │
              ▼
     Structured AI Review
              │
        ┌─────┴─────┐
        ▼           ▼
     GitHub      Supabase
     Feedback    Persistence
                    │
                    ▼
                 Analytics
```

Heavy AI processing is performed asynchronously rather than inside the GitHub webhook request.

---

# 🏗️ System Architecture

```text
                       ┌──────────────────┐
                       │    GitHub PR     │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │     FastAPI      │
                       │ Webhook Gateway  │
                       │ HMAC Validation  │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │      Redis       │
                       │   Task Broker    │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Celery Worker   │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │    LangGraph     │
                       │        +         │
                       │     Gemini AI    │
                       └────────┬─────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌───────────────┐       ┌───────────────┐
            │ GitHub Review │       │   Supabase    │
            │   Feedback    │       │ Review History│
            └───────────────┘       └───────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │   Streamlit   │
                                    │Command Center │
                                    └───────────────┘
```

---

# 📊 Command Center

Aegis AI includes a Streamlit-based Command Center.

It provides two main areas:

### 🔍 Live Code Sandbox

Submit standalone code and receive:

- Overall score
- Risk level
- Executive summary
- Validated pros
- Structured findings
- Severity classification
- Finding category
- Confidence level
- Issue-linked fixes
- Refactored code

### 📊 Analytics

Review historical activity stored in Supabase and monitor code-review activity across repositories.

---

# 🛠️ Technology Stack

| Technology | Role |
|---|---|
| **Python** | Core application language |
| **Google Gemini** | AI code analysis |
| **LangGraph** | Review workflow orchestration |
| **FastAPI** | API and GitHub webhook gateway |
| **Celery** | Background processing |
| **Redis** | Task broker |
| **Supabase** | Review persistence |
| **Streamlit** | Command Center |
| **GitHub API** | Pull-request integration |
| **Pydantic** | Structured AI output validation |
| **Pytest** | Automated testing |
| **GitHub Actions** | Continuous integration |

---

# 📂 Project Structure

```text
ai-reviewer/
│
├── .github/
│   └── workflows/
│
├── examples/
├── tests/
│
├── main.py
├── graph.py
├── tasks.py
├── dashboard.py
│
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

### `main.py`

FastAPI backend responsible for:

- GitHub webhook handling
- HMAC signature verification
- Manual review API
- API authentication
- Request validation

### `graph.py`

Contains the AI review workflow, including:

- Security analysis
- Performance analysis
- Structured findings
- Severity classification
- Confidence classification
- Pros generation
- Refactoring
- Score and risk generation
- Final report formatting

### `tasks.py`

Handles asynchronous GitHub review operations:

- PR diff retrieval
- AI review execution
- GitHub feedback
- Supabase persistence

### `dashboard.py`

Provides the Streamlit Command Center:

- Live Code Sandbox
- Review reports
- Code scores
- Risk levels
- Analytics

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/parasbishnoi029/ai-reviewer.git
cd ai-reviewer
```

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

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ⚙️ Environment Configuration

Create a `.env` file:

```env
GOOGLE_API_KEY=your_gemini_api_key

GITHUB_TOKEN=your_github_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret

API_KEY=your_api_key

REDIS_URL=redis://localhost:6379/0

SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
```

> Never commit API keys, access tokens, webhook secrets, or production credentials.

---

# ▶️ Running Aegis AI

### Start Redis

```bash
redis-server
```

### Start FastAPI

```bash
uvicorn main:app --reload
```

### Start Celery

```bash
celery -A tasks.celery_app worker --loglevel=info
```

### Start the Command Center

```bash
streamlit run dashboard.py
```

Typical local endpoints:

```text
FastAPI:
http://localhost:8000

API Documentation:
http://localhost:8000/docs

Streamlit:
http://localhost:8501
```

---

# 🔗 GitHub Webhook Setup

Navigate to:

```text
GitHub Repository
      ↓
Settings
      ↓
Webhooks
      ↓
Add webhook
```

Configure:

```text
Payload URL:
https://YOUR-DEPLOYED-API/github-webhook
```

Use the same secret configured in:

```env
GITHUB_WEBHOOK_SECRET=...
```

Enable pull-request events.

---

# 🧪 Testing

Run:

```bash
pytest tests/
```

GitHub Actions can automatically execute repository checks when code is pushed or pull requests are created.

---

# 🔐 Security

Aegis AI includes several security controls around its infrastructure:

### HMAC Webhook Authentication

Incoming GitHub webhooks are verified using HMAC SHA-256.

### API Authentication

Manual review requests require API-key authentication.

### Request Size Limits

Large code submissions and PR diffs are restricted to reduce excessive AI workloads.

### Network Timeouts

External API requests use explicit timeouts.

### Structured AI Responses

Important AI results are constrained using structured Pydantic models rather than relying entirely on free-form output.

---

# ✅ Current Capabilities

- [x] AI-assisted code review
- [x] Overall Code Quality Score
- [x] Risk-level classification
- [x] Executive review summary
- [x] Validated pros
- [x] Security analysis
- [x] Performance analysis
- [x] Structured findings
- [x] Severity classification
- [x] Finding categories
- [x] Confidence classification
- [x] Issue-linked fixes
- [x] Refactored code generation
- [x] LangGraph workflow
- [x] Gemini integration
- [x] FastAPI backend
- [x] GitHub webhook integration
- [x] HMAC webhook validation
- [x] Automated PR reviews
- [x] Celery background processing
- [x] Redis task broker
- [x] Supabase persistence
- [x] Streamlit Command Center
- [x] Review analytics
- [x] Automated testing
- [x] GitHub Actions CI

---

# 🗺️ Roadmap

The next phase focuses on making reviews more context-aware, reliable, and actionable.

### AI Review Engine

- [ ] Parallel Security, Performance, Quality, and Testing agents
- [ ] Repository-aware context retrieval
- [ ] Related-file and dependency context
- [ ] Finding deduplication
- [ ] Better false-positive filtering
- [ ] Prompt-injection defenses
- [ ] Deterministic score calibration
- [ ] Review validation/evaluation stage

### GitHub Integration

- [ ] File and line-level findings
- [ ] Inline GitHub suggestions
- [ ] Automated PR verdicts
- [ ] Duplicate webhook protection
- [ ] Repository-specific `.aegis.yml` policies

### Platform Engineering

- [ ] Docker support
- [ ] Docker Compose
- [ ] Health and readiness endpoints
- [ ] Advanced Celery retry policies
- [ ] Expanded test coverage
- [ ] Ruff linting
- [ ] Static type checking
- [ ] Dependency vulnerability scanning

### Analytics

- [ ] Average review score
- [ ] Score history
- [ ] Risk distribution
- [ ] Severity distribution
- [ ] Finding-category trends
- [ ] Review latency
- [ ] Failure rate
- [ ] AI token usage
- [ ] Estimated AI cost

---

# ⚠️ Limitations

Aegis AI uses a large language model to assist with code analysis.

AI-generated reviews can contain:

- False positives
- Missed vulnerabilities
- Incorrect severity classifications
- Incorrect confidence estimates
- Unnecessary optimizations
- Incorrect refactoring recommendations
- Imperfect quality scores

Aegis AI should therefore be treated as an **engineering assistant**, not as a replacement for:

- Human code review
- Automated tests
- Static-analysis tools
- Dependency scanners
- Security testing
- Professional security audits

Always inspect and test generated code before using it in production.

---

# 🎯 Design Principle

> **AI should assist engineering judgment, not replace it.**

Aegis AI combines AI-assisted reasoning with conventional backend engineering to make code reviews faster, structured, and more actionable.

---

# 🤝 Contributing

Contributions and suggestions are welcome.

```text
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add or update tests
5. Open a pull request
```

---

# 📄 License

This project is licensed under the **MIT License**.

See `LICENSE` for details.

---

# 👨‍💻 Author

**Paras**

GitHub: **@parasbishnoi029**

---

## ⭐ Support

If you find Aegis AI useful, consider starring the repository.

---

### 🛡️ Aegis AI

**Analyze. Score. Explain. Fix.**
