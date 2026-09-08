# AgentSwarm

## Multi-Agent Task Orchestration Engine

[![Live Demo](https://img.shields.io/badge/Live%20Demo-AgentSwarm%20Web-00E599?style=for-the-badge&logo=render&logoColor=white)](https://agentswarm-web.onrender.com)
[![API Status](https://img.shields.io/badge/Live%20API-FastAPI%20Swagger-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://agentswarm-api.onrender.com/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> 🌐 **Live Web Application**: [https://agentswarm-web.onrender.com](https://agentswarm-web.onrender.com)  
> ⚡ **Live Backend API**: [https://agentswarm-api.onrender.com](https://agentswarm-api.onrender.com)  
> 📚 **Interactive Swagger API Docs**: [https://agentswarm-api.onrender.com/docs](https://agentswarm-api.onrender.com/docs)  
> 📖 **Interactive ReDoc**: [https://agentswarm-api.onrender.com/redoc](https://agentswarm-api.onrender.com/redoc)  

AgentSwarm is a **stateful multi-agent AI platform** that decomposes user requests into smaller tasks and coordinates specialized AI agents to complete them.

The system uses **LangGraph** to control the workflow, **FastAPI** for the backend API, **PostgreSQL** for persistence and checkpointing, and **React** for the frontend.

Instead of relying on a single AI call, AgentSwarm separates planning, research, coding, content generation, evaluation, human review, and finalization into different stages.

---

## What AgentSwarm Does

A user provides a natural-language goal:

```text
Build a Python implementation of a graph algorithm
and explain its complexity.
````

AgentSwarm then:

```text
User Request
     │
     ▼
   Planner
     │
     ├──────────────┬──────────────┐
     ▼              ▼              ▼
 Researcher       Coder         Content
     │              │              │
     └──────────────┴──────────────┘
                    │
                    ▼
                Evaluator
                    │
              ┌─────┴─────┐
              │           │
            PASS        REVISE
              │           │
              ▼           ▼
        Human Review    Worker
              │           │
        ┌─────┴─────┐     │
        │           │     │
     APPROVE      REJECT  │
        │           │     │
        ▼           └─────┘
     Finalizer
        │
        ▼
   Final Output
```

```mermaid
flowchart TD
    User([User Request]) --> Planner[Planner Agent]
    Planner --> Router{Task Router}
    Router -->|Research Task| Researcher[Researcher Agent]
    Router -->|Coding Task| Coder[Coder Agent]
    Router -->|Content Task| Content[Content Agent]
    Researcher --> Complete[Mark Task Complete]
    Coder --> Complete
    Content --> Complete
    Complete --> Next{More Tasks?}
    Next -->|Yes| Router
    Next -->|No| Evaluator[RAG Evaluator - Gemini 3.6 Flash]
    Evaluator --> EvalCheck{Verdict}
    EvalCheck -->|REVISE| Revision[Revision Worker]
    EvalCheck -->|UNAVAILABLE| EndUnavail([Status: EVALUATION_UNAVAILABLE])
    EvalCheck -->|PASS| HumanReview[Human Review HITL Node]
    HumanReview --> HumanDecision{Human Decision}
    HumanDecision -->|REJECT with Feedback| Revision
    HumanDecision -->|APPROVE| Finalizer[Finalizer Agent]
    Revision -->|Re-eval Loop| Evaluator
    Finalizer --> Output([Final Result & Artifacts])
```

This ensures each stage focuses on its specialized domain with rigorous verification.

---

# Key Features

* Multi-agent task planning
* Specialized AI workers
* Stateful LangGraph orchestration
* Web research using Tavily
* AI-powered code generation
* Content and explanation generation
* Independent output evaluation
* Automatic bounded revision loop
* Human-in-the-loop approval
* PostgreSQL persistence
* LangGraph PostgreSQL checkpointing
* JWT authentication
* User-specific task authorization
* Task monitoring and management
* Task stopping and deletion
* Secure artifact storage
* Artifact downloads
* Secure task sharing
* React workflow dashboard
* Evaluator quota/error handling
* Automated local workflow tests

---

# Architecture

AgentSwarm is organized into several layers.

```text
┌─────────────────────────────────────────────────────┐
│                    React Frontend                   │
│        Dashboard • Workflow • Tasks • Artifacts     │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                    FastAPI API                      │
│   Authentication • Tasks • Approval • Artifacts    │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  Task Runner                        │
│          Background Task Execution                  │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                   LangGraph                         │
│              Stateful Workflow Engine               │
└──────────────────────────┬──────────────────────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        Researcher       Coder        Content
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                       Evaluator
                           │
                    Human Review
                           │
                           ▼
                       Finalizer
                           │
                           ▼
                      Artifacts
                           │
                           ▼
                      PostgreSQL
```

---

# Agent Roles

## Planner

The Planner receives the user's goal and creates a structured execution plan.

It determines:

* What tasks need to be performed
* Which agent should perform each task
* The task type
* Task dependencies

Supported worker types include:

* Research
* Coding
* Content
* Questions

The generated plan is validated before execution.

---

## Researcher

The Researcher performs external web research using **Tavily**.

Its output provides research evidence that can be used by downstream agents.

```text
Research Task
      │
      ▼
Tavily Search
      │
      ▼
Research Evidence
```

---

## Coder

The Coder handles implementation tasks.

It receives:

* User goal
* Current task
* Research
* Previous evaluator feedback
* Human feedback

During revisions, it uses the available feedback to improve the implementation while preserving work that is already correct.

Coding results can also be stored as downloadable artifacts.

---

## Content Agent

The Content Agent handles tasks such as:

* Explanations
* Summaries
* Written content
* Questions
* Supporting documentation

---

## Evaluator

The Evaluator independently reviews worker output.

AgentSwarm separates the generation and evaluation models:

```text
Worker Agents
     │
     ▼
Groq: openai/gpt-oss-120b
     │
     ▼
Evaluator
     │
     ▼
Gemini: gemini-3.6-flash
```

The Evaluator can determine whether the result should pass or be revised.

---

## Human Review

After automated evaluation, the workflow can pause for human approval.

The user can:

* Approve the result
* Reject the result
* Provide feedback for revision

```text
Evaluator
    │
    ▼
Human Review
   /       \
  /         \
Approve     Reject
  │           │
  ▼           ▼
Finalizer   Revision
               │
               ▼
           Evaluator
```

---

## Finalizer

The Finalizer produces the final user-facing response after the required workflow stages have completed.

It uses the available:

* Research
* Generated content
* Code
* Evaluation
* User goal

Approved implementations are preserved rather than unnecessarily rewritten.

---

# Revision System

AgentSwarm supports a bounded revision loop.

```text
             ┌─────────────┐
             │    Worker   │
             └──────┬──────┘
                    │
                    ▼
             ┌─────────────┐
             │  Evaluator  │
             └──────┬──────┘
                    │
             ┌──────┴──────┐
             │             │
            PASS         REVISE
             │             │
             ▼             ▼
       Human Review      Worker
                            │
                            ▼
                        Evaluator
```

The number of automatic revisions is limited to prevent infinite workflow loops.

Human rejection can also trigger a bounded revision.

---

# Stateful Workflow

LangGraph maintains a shared `AgentState` throughout execution.

The state contains information including:

```text
User Goal
Plan
Plan Tasks
Current Task
Completed Tasks
Research
Code
Content
Evaluation
Revision Count
Human Approval
Human Feedback
Revision Reason
Final Answer
Workflow Status
```

This allows different agents to work on the same evolving task context.

---

# Persistence

AgentSwarm uses **PostgreSQL** for application data and LangGraph checkpointing.

Persistent information includes:

* User accounts
* Tasks
* Task status
* Plans
* Research
* Generated code
* Generated content
* Evaluations
* Revision information
* Human feedback
* Final answers
* Task sharing information

The workflow state can therefore be persisted instead of existing only during a single process execution.

---

# Artifact System

Generated implementation files are stored separately from the workflow state.

```text
artifacts/
└── generated/
    └── <task_id>/
        ├── task_<id>_code.txt
        └── task_<id>_revision_<n>_code.txt
```

The artifact manager provides:

* Task-specific storage
* Filename validation
* Path traversal protection
* Maximum artifact size limits
* Artifact listing
* Artifact downloading
* Artifact deletion

Artifacts are associated with individual tasks and protected by task ownership checks.

---

# Authentication

AgentSwarm uses JWT-based authentication.

Supported functionality:

* User signup
* User login
* JWT access tokens
* Protected API endpoints
* Password reset
* Account deletion

Task operations verify that the authenticated user owns the requested task.

---

# Task Management

Users can:

* Create tasks
* View tasks
* Monitor task status
* Stop running tasks
* Approve or reject tasks
* Provide revision feedback
* View generated artifacts
* Download artifacts
* Share completed tasks
* Delete terminal tasks

---

# Task States

Tasks can move through states such as:

```text
STARTING
   │
   ▼
RUNNING
   │
   ├───────────────┐
   │               │
   ▼               ▼
REVISING     WAITING_FOR_HUMAN
   │               │
   │          ┌────┴────┐
   │          │         │
   │       APPROVE    REJECT
   │          │         │
   └──────────┼─────────┘
              │
              ▼
          FINALIZER
              │
              ▼
          COMPLETED
```

Other terminal states include:

```text
FAILED
STOPPED
EVALUATION_UNAVAILABLE
```

Terminal-state protection prevents stopped tasks from being accidentally overwritten during later synchronization.

---

# External Services

## Groq

Used by the primary worker agents:

```text
openai/gpt-oss-120b
```

Used for:

* Planning
* Research-related generation
* Coding
* Content generation
* Finalization

---

## Google Gemini

Used by the Evaluator:

```text
gemini-3.6-flash
```

Using a separate model for evaluation provides model diversity between generation and verification.

---

## Tavily

Used by the Researcher for web search and external information gathering.

---

# RAG Support

The Evaluator can retrieve relevant information from the project's document knowledge base before evaluating generated output.

This provides additional context for evaluation instead of relying only on the worker's response.

---

# Evaluator Failure Handling

External AI services can become unavailable because of:

* API quotas
* Rate limits
* Temporary service failures

AgentSwarm distinguishes evaluator failure from successful evaluation.

For example:

```text
EVALUATION_UNAVAILABLE
```

means that the worker output could not be verified by the Evaluator.

The workflow does **not** treat an unavailable evaluator as a successful evaluation.

---

# API

| Method   | Endpoint                           | Purpose                |
| -------- | ---------------------------------- | ---------------------- |
| `GET`    | `/health`                          | Health check           |
| `POST`   | `/auth/signup`                     | Create account         |
| `POST`   | `/auth/login`                      | Login                  |
| `POST`   | `/auth/forgot-password`            | Request password reset |
| `POST`   | `/auth/reset-password`             | Reset password         |
| `DELETE` | `/auth/account`                    | Delete account         |
| `POST`   | `/tasks`                           | Create task            |
| `GET`    | `/tasks`                           | List user's tasks      |
| `GET`    | `/tasks/{id}`                      | Get task               |
| `POST`   | `/tasks/{id}/stop`                 | Stop task              |
| `POST`   | `/tasks/{id}/approval`             | Approve/reject task    |
| `GET`    | `/tasks/{id}/artifacts`            | List artifacts         |
| `GET`    | `/tasks/{id}/artifacts/{filename}` | Download artifact      |
| `POST`   | `/tasks/{id}/share`                | Create share token     |
| `GET`    | `/share/{token}`                   | View shared task       |
| `DELETE` | `/tasks/{id}`                      | Delete task            |

FastAPI provides interactive API documentation at:

```text
http://localhost:8000/docs
```

---

# Technology Stack

| Layer           | Technology                   |
| --------------- | ---------------------------- |
| Frontend        | React, Vite, JavaScript, CSS |
| Backend         | Python, FastAPI              |
| Orchestration   | LangGraph                    |
| AI Framework    | LangChain                    |
| Worker Model    | Groq `openai/gpt-oss-120b`   |
| Evaluator Model | Gemini `gemini-3.6-flash`    |
| Web Research    | Tavily                       |
| Database        | PostgreSQL                   |
| ORM             | SQLAlchemy                   |
| Database Driver | Psycopg                      |
| Validation      | Pydantic                     |
| Authentication  | JWT                          |

---

# Project Structure

```text
AgentSwarm/
│
├── agents/
│   ├── planner.py
│   ├── researcher.py
│   ├── coder.py
│   ├── content.py
│   ├── evaluator.py
│   └── finalizer.py
│
├── api/
│   ├── api.py
│   └── schemas.py
│
├── artifacts/
│   ├── __init__.py
│   └── manager.py
│
├── auth/
│   ├── dependencies.py
│   ├── routes.py
│   └── security.py
│
├── database/
│   ├── connection.py
│   └── models.py
│
├── graph/
│   ├── human.py
│   ├── nodes.py
│   ├── state.py
│   └── workflow.py
│
├── services/
│   └── task_runner.py
│
├── tools/
│   └── web_search.py
│
├── tests/
│   ├── test_artifacts_local.py
│   ├── test_task_sync.py
│   └── test_workflow_routing.py
│
├── frontend/
│   └── ...
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
DATABASE_URL=your_postgresql_connection_string
SECRET_KEY=your_jwt_secret
```

Replace the placeholder values with your actual credentials.

**Never commit `.env` to Git.**

The repository ignores:

```gitignore
venv/
.env
__pycache__/
*.pyc
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/suhas-2007/AgentSwarm.git
cd AgentSwarm
```

## 2. Create a Virtual Environment

```powershell
python -m venv venv
```

## 3. Install Backend Dependencies

```powershell
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Create `.env` and configure:

```text
GROQ_API_KEY
GEMINI_API_KEY
TAVILY_API_KEY
DATABASE_URL
SECRET_KEY
```

## 5. Start the Backend

```powershell
.\venv\Scripts\python.exe -m uvicorn api.api:app --reload
```

## 6. Start the Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm.cmd run dev
```

---

# Automated Test Suite

AgentSwarm maintains a rigorous **64-test automated test suite** with 100% pass rate, covering every workflow permutation, edge case, and security boundary.

### Running the Test Suite

```powershell
# Run the complete test suite with verbose output
$env:PYTHONPATH = "C:\Users\suhas\OneDrive\Desktop\AgentSwarm"
.\venv\Scripts\pytest.exe -v
```

### Test Coverage Breakdown

| Category | Test File | Description | Count |
| :--- | :--- | :--- | :--- |
| **Workflow Routing** | `test_workflow_routing.py` | Validates task router dispatching to Researcher, Coder, Evaluator, and proper conditional routing. | 13 |
| **Edge Cases & Failure Recovery** | `test_workflow_edge_cases.py` | Worker failures $\rightarrow$ `FAILED`, user stop protection against overwriting, evaluator unavailable routing, human reject loop, max revisions. | 8 |
| **Security & Task Isolation** | `test_security_api.py` | Cross-user task isolation (404), unauthenticated blocking, share token sanitization, and auth password validation. | 3 |
| **Human-in-the-Loop Review** | `test_task_approval_api.py` | Human approval flow, rejection with mandatory feedback, rejection without feedback validation (400). | 3 |
| **Revision & Limits** | `test_revision_limit.py`, `test_revision.py` | Evaluator max revision caps (`MAX_REVISIONS = 2`), human rejection limit routing to `END`, revision counter increments. | 3 |
| **Task Synchronization & Stop** | `test_task_sync.py` | State synchronization from checkpoints, terminal state protection, partial state preservation. | 5 |
| **Planner Decomposition** | `test_planner.py` | Verifies plan decomposition for coding, research, content, and restricts invalid task agents. | 7 |
| **RAG Knowledge Base** | `test_rag.py` | Document chunking, ChromaDB vector collection reset, document retrieval, and metadata preservation. | 4 |
| **Task Lifecycle & Workflow APIs**| `test_tasks_api.py`, `test_tasks_workflow_api.py` | API validation, task submission, background runner invocation, and status transitions. | 5 |
| **Persistence & Checkpoints** | `test_checkpoint.py`, `test_checkpoint_persistence.py` | PostgreSQL checkpointer integration, snapshot recovery, and thread-specific states. | 3 |
| **Full End-to-End Workflows** | `test_full_workflow.py`, `test_full_revision.py` | Multi-step end-to-end execution from Planner $\rightarrow$ Worker $\rightarrow$ Evaluator $\rightarrow$ Revision $\rightarrow$ Approval $\rightarrow$ Finalizer. | 10 |

---

# Execution Walkthroughs

AgentSwarm is designed to handle complex, branching multi-agent lifecycles with deterministic controls. Below are 3 real-world execution traces:

### Scenario 1: Clean Coding Task (Passes on First Try)

**Goal**: *"Write an efficient Python function to detect cycles in a directed graph using Kahn's topological sort."*

```text
[1. START]      User submits goal via POST /tasks
                 └── Task #101 created with status: STARTING
[2. PLANNER]    Planner decomposes goal into structured plan:
                 └── Task 1: "coder" - Implement Kahn's cycle detection algorithm
[3. WORKER]     Coder generates cycle detection Python module with unit tests & docstrings
                 └── Output saved to artifacts/generated/101/task_101_code.txt
                 └── Status transitions: CODING → EVALUATING
[4. EVALUATOR]  Evaluator checks correctness, algorithmic complexity (O(V+E)), and formatting:
                 └── Evaluator outputs: "VERDICT: PASS - Kahn's algorithm correctly tracks in-degrees"
                 └── Status transitions: EVALUATING → WAITING_FOR_HUMAN
[5. HITL REVIEW] User inspects result in React Dashboard, reviews code, and clicks "Approve & Finalize":
                 └── POST /tasks/101/approval with {"approved": true}
[6. FINALIZER]  Finalizer packages solution with markdown explanation and complexity summary
                 └── Final status: COMPLETED (Revision count: 0)
```

---

### Scenario 2: Research & Content Task with Human Rejection & Revision

**Goal**: *"Research quantum computing breakthroughs in 2024 and write an executive summary for non-technical leadership."*

```text
[1. START]      User submits goal via POST /tasks
[2. PLANNER]    Planner creates two-phase plan:
                 └── Task 1: "researcher" - Query Tavily for 2024 quantum announcements
                 └── Task 2: "content" - Draft executive summary using research findings
[3. WORKER 1]   Researcher queries Tavily for recent neutral atom and fault-tolerant quantum milestones
                 └── Research findings compiled into structured state
[4. WORKER 2]   Content agent writes initial executive summary
[5. EVALUATOR]  Evaluator verifies factual consistency: "VERDICT: PASS"
                 └── Status transitions to WAITING_FOR_HUMAN
[6. HITL REVIEW] User reviews draft but needs a financial implications section:
                 └── User enters feedback: "Include estimated commercial timeline and market impact"
                 └── User clicks "Ask for improvements" (Reject)
                 └── Status transitions to REVISING (Revision count: 1/2)
[7. REVISION]   Content worker re-invoked with user feedback:
                 └── Injects section on commercial timeline (2028-2030) and enterprise risk
[8. EVALUATOR]  Evaluator re-evaluates updated draft: "VERDICT: PASS"
[9. HITL REVIEW] User reviews revised draft and clicks "Approve & Finalize"
[10. FINALIZER] Final answer assembled and presented to user. Status: COMPLETED.
```

---

### Scenario 3: Task Interruption & User Stop Safeguard

**Goal**: *"Generate a comprehensive 100-page market analysis of renewable energy in South America."*

```text
[1. START]      User submits goal via POST /tasks
[2. RUNNING]    Planner creates extensive plan; Researcher starts long-running web searches
[3. USER STOP]  User realizes prompt was overly broad and clicks "Stop Task" in Dashboard
                 └── API executes: POST /tasks/105/stop
                 └── Database updates Task #105 atomically: status = "STOPPED", current_task_id = null
[4. SAFEGUARD]  The background TaskRunner thread attempts to sync checkpoint state:
                 └── sync_task_from_state executes: UPDATE tasks WHERE id=105 AND status != 'STOPPED'
                 └── Row count = 0: STOPPED status is completely immune to being overwritten!
[5. TERMINAL]   Task remains safely in STOPPED state; user can delete or resubmit without data corruption.
```

---

# RAG Knowledge Base & Evaluator Architecture

AgentSwarm uses an **isolated multi-model architecture** to ensure objective evaluation:

* **Generation Engine**: High-throughput open weights via Groq (`openai/gpt-oss-120b`).
* **Evaluation Engine**: Multimodal reasoner via Google Gemini (`gemini-3.6-flash`).

### Evaluation Workflow

```text
Worker Output + Ground Truth Docs
              │
              ▼
   ChromaDB Vector Retrieval
              │
              ▼
   Gemini 3.6 Flash Evaluator
              │
    ┌─────────┴─────────┐
    ▼                   ▼
VERDICT: PASS       VERDICT: REVISE
```

1. **Document Ingestion**: Reference files and project documents are chunked (500 characters, 50 overlap) and indexed in ChromaDB.
2. **Context Retrieval**: When evaluating worker outputs, the Evaluator queries the vector store for authoritative guidelines and reference implementations.
3. **Structured Verdict**: The Evaluator outputs either `VERDICT: PASS` or `VERDICT: REVISE` with targeted feedback.
4. **Quota Resilience (`EVALUATION_UNAVAILABLE`)**: If external API rate limits or quota boundaries are encountered (HTTP 429/503), AgentSwarm traps the error and marks the status as `EVALUATION_UNAVAILABLE` rather than falsely passing unverified output.

---

# Security & Isolation Hardening

AgentSwarm implements defense-in-depth across API, database, and file system boundaries:

* **Strict Task Isolation**: Every private endpoint enforces `Task.user_id == current_user.id`. Requests targeting another user's task ID return `404 Not Found` to prevent resource enumeration.
* **Share Token Sanitization**: Public task sharing (`/share/{token}`) is restricted strictly to `COMPLETED` tasks. Non-completed tasks return `403 Forbidden`. The response only exposes public fields (`task_id`, `goal`, `status`, `evaluation`, `final_answer`, `revision_count`), never leaking user emails, user IDs, or internal checkpoint metadata.
* **Password & Token Security**: Passwords enforce a minimum 8-character policy. Password reset tokens are generated using cryptographically secure random bytes (`secrets.token_urlsafe`), and only SHA-256 hashes are stored in PostgreSQL with time-based expiration (`reset_token_expires_at`).
* **Artifact Path Traversal Protection**: Filenames are validated against directory traversal attacks (`..`, absolute paths, illegal characters). Artifacts are strictly quarantined within per-task directories (`artifacts/generated/<task_id>/`).

---

# Production Deployment Guide

For a full step-by-step walkthrough of deploying to **Render** or **Railway**, see the [DEPLOYMENT.md](DEPLOYMENT.md) guide.

### 1-Click Blueprint (Render)
AgentSwarm includes an Infrastructure-as-Code [render.yaml](render.yaml) specification that provisions the managed PostgreSQL database, FastAPI backend, and React static site automatically.

### Environment Configuration

AgentSwarm requires standard environment variables. Copy the template and fill in your credentials:

```powershell
copy .env.example .env
```

> [!IMPORTANT]
> Never commit your `.env` file or hardcode actual API keys into source files. All configuration is loaded dynamically via `python-dotenv`. In production, set these variables in your hosting provider's dashboard.

### Docker Container Deployment

To containerize the FastAPI backend for production:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg3 and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### PostgreSQL 16 Setup

AgentSwarm requires a PostgreSQL database for application state and LangGraph checkpointing:

```sql
CREATE DATABASE agentswarm;
CREATE USER agentswarm_user WITH ENCRYPTED PASSWORD 'secure_production_password';
GRANT ALL PRIVILEGES ON DATABASE agentswarm TO agentswarm_user;
```

Update your `.env`:

```env
DATABASE_URL=postgresql://agentswarm_user:secure_production_password@db.example.com:5432/agentswarm
```

### Frontend Production Build & Hosting

```bash
cd frontend
npm install
npm run build
```

The resulting `frontend/dist/` directory can be hosted behind Nginx, Cloudflare Pages, AWS S3 + CloudFront, or Vercel:

```nginx
# Sample Nginx reverse proxy configuration
server {
    listen 80;
    server_name agentswarm.example.com;

    root /var/www/agentswarm/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

# Live Cloud Deployment

AgentSwarm is deployed and live on **Render** using an automated Infrastructure-as-Code Blueprint ([`render.yaml`](./render.yaml)):

| Component | Status | Production URL |
| :--- | :---: | :--- |
| **Frontend Web App** | [![Status](https://img.shields.io/badge/Live-00E599?style=flat-square&logo=render&logoColor=white)](https://agentswarm-web.onrender.com) | [https://agentswarm-web.onrender.com](https://agentswarm-web.onrender.com) |
| **FastAPI Backend API** | [![Status](https://img.shields.io/badge/Live-009688?style=flat-square&logo=fastapi&logoColor=white)](https://agentswarm-api.onrender.com) | [https://agentswarm-api.onrender.com](https://agentswarm-api.onrender.com) |
| **Interactive Swagger Docs** | [![Status](https://img.shields.io/badge/Docs-Swagger-blue?style=flat-square)](https://agentswarm-api.onrender.com/docs) | [https://agentswarm-api.onrender.com/docs](https://agentswarm-api.onrender.com/docs) |
| **PostgreSQL Database** | [![Status](https://img.shields.io/badge/Managed-PostgreSQL%2018-blue?style=flat-square&logo=postgresql&logoColor=white)](https://render.com) | Managed Render Cloud DB + LangGraph Checkpointer |

### Key Production Capabilities:
* **Google Identity Services (OAuth 2.0)**: Secure passwordless sign-in with Google.
* **Bring-Your-Own-Key (BYOK) Credit Control**: Users manage their own Gemini, Groq, and Tavily API keys directly from the dashboard modal to protect host quota.
* **PostgreSQL Stateful Checkpointing**: Distributed workflow state preservation across worker instances.

---

# Design Principles

### Specialized Agents
Each agent has a focused responsibility instead of one model performing every operation.

### Explicit Workflow State
Agent communication occurs through structured LangGraph state (`AgentState`).

### Independent Evaluation
The Evaluator is separated from the primary worker model, leveraging cross-model verification.

### Controlled Autonomy
Revision attempts are bounded by `MAX_REVISIONS = 2` to prevent runaway API consumption.

### Human Oversight
Human approval is required before finalization, with mandatory feedback on rejection.

### Persistent Execution
Workflow state is checkpointed in PostgreSQL via `PostgresSaver`, enabling robust task resumption.

---

# License

MIT License

---

## Author

**Raavi Suhas**

GitHub: [https://github.com/suhas-2007/AgentSwarm](https://github.com/suhas-2007/AgentSwarm)

