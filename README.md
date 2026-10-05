# AgentSwarm

## Multi-Agent Task Runner & Workflow System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-AgentSwarm%20Web-00E599?style=for-the-badge&logo=render&logoColor=white)](https://agentswarm-web.onrender.com)
[![API Status](https://img.shields.io/badge/Live%20API-FastAPI%20Swagger-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://agentswarm-api.onrender.com/docs)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> 🌐 **Live Web Application**: [https://agentswarm-web.onrender.com](https://agentswarm-web.onrender.com)  
> ⚡ **Live Backend API**: [https://agentswarm-api.onrender.com](https://agentswarm-api.onrender.com)  
> 📚 **Interactive Swagger API Docs**: [https://agentswarm-api.onrender.com/docs](https://agentswarm-api.onrender.com/docs)  
> 📖 **Interactive ReDoc**: [https://agentswarm-api.onrender.com/redoc](https://agentswarm-api.onrender.com/redoc)  

AgentSwarm is a full-stack multi-agent project I built to solve a problem I kept running into: single LLM prompts usually try to do way too much at once, get confused, hallucinate code, or just fail silently. 

Instead of asking one model to plan, code, search the web, and verify everything in one shot, I built this system to break a goal into smaller bite-sized jobs. Each job gets routed to a specialized agent, saves its progress into a real PostgreSQL database through LangGraph, gets checked by a totally separate evaluator LLM, and finally asks you (the human) to give the thumbs up before finishing.

---

## What AgentSwarm Does

Whenever you type in a prompt on the dashboard, like:

```text
Build a Python implementation of a graph algorithm
and explain its complexity.
```

Here is what happens behind the scenes:

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

Breaking down the workflow this way means the coder only writes code, the researcher only gathers live sources, and the evaluator gives an unbiased review.

---

# Key Features

* Breaks down prompts into a sensible step-by-step plan
* Specialized worker agents for coding, web research, and writing explanations
* Workflow execution managed by LangGraph state machines
* Live web searching powered by the Tavily API
* Fast code generation on Groq running `openai/gpt-oss-120b`
* Automatic content drafting and markdown formatting
* Independent evaluation using Google Gemini (`gemini-3.6-flash`)
* Built-in revision loops with a hard cap to stop infinite loops
* Human-in-the-loop review where you can approve or send feedback to fix things
* Real database persistence with PostgreSQL and SQLAlchemy
* Resumable LangGraph checkpoints stored in Postgres tables
* Secure user authentication with JWT tokens and bcrypt password hashing
* Full user isolation so nobody can peek at or edit someone else's tasks
* Live task status polling and step-by-step UI updates
* Emergency task stop button that locks state in the database
* File artifact generator that saves code files safely on disk
* Direct browser downloads for generated code and output files
* Public share links that only expose clean completed work
* Interactive React dashboard built with Vite
* Graceful fallback states if third-party LLM quotas run dry
* Full 64-test automated suite written in Pytest

---

# Architecture

I structured the project into clean layers so the frontend, backend APIs, graph execution, and database stay decoupled:

```text
┌─────────────────────────────────────────────────────┐
│                    React Frontend                   │
│        Dashboard • Workflow • Tasks • Artifacts     │
│             (Vite + React 19 + Vanilla CSS)         │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                    FastAPI API                      │
│   Authentication • Tasks • Approval • Artifacts     │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  Task Runner                        │
│          Background Task Execution Thread           │
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

When you type a goal, the Planner is the very first agent to wake up. It parses your prompt and outputs a clean JSON array of subtasks.

It decides:

* What exact tasks need to be completed
* Which agent is best suited for each step
* The task category (research, coding, content, questions)
* What order they should run in

I wrote strict prompt rules so the planner never invents evaluator or finalizer tasks on its own, because the workflow handles those automatically.

---

## Researcher

Whenever a task needs up-to-date documentation, real-world data, or facts, the Planner calls the Researcher.

It uses the **Tavily Search API** to look up queries on the live web, extracts the most relevant snippets, and puts them into the shared workflow state so the coder or writer can read them.

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

The Coder is responsible for generating working software. It runs on Groq using `openai/gpt-oss-120b` so it writes code in seconds.

It takes in:

* Your original goal
* The specific task description from the plan
* Any research notes gathered by the Researcher
* Any criticism from the Evaluator (if it's a revision)
* Any notes you typed during human review

Whenever the Coder finishes, its code gets saved both in the state and as a standalone file in the `artifacts/generated/` folder.

---

## Content Agent

Not everything is code. When you ask for explanations, study guides, comparisons, or summaries, the Content agent takes over.

It produces clean GitHub-flavored markdown with headers, bullet points, and code snippets where needed.

---

## Evaluator

This is one of the most important parts of the project. If you let an LLM grade its own homework, it almost always says "everything looks great!" even when there are obvious bugs.

To fix that, I split the models:

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

The Evaluator inspects the code or content against your goal and against local reference docs using RAG. It then outputs either `VERDICT: PASS` or `VERDICT: REVISE` with clear bullet points explaining what needs fixing.

---

## Human Review

Even with automated evaluation, having a human in the loop makes a huge difference. When the Evaluator gives a PASS verdict, LangGraph pauses the execution using an interrupt.

In the React UI, you'll see an approval card with two buttons:

* **Approve & Finalize**: moves the task to the Finalizer
* **Ask for Changes**: lets you type custom feedback (e.g. "make the function async" or "add input validation") and sends it back to the worker

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

Once everything is approved, the Finalizer agent bundles the pieces together into the finished answer you see on your screen. It leaves working code intact and writes a concise final wrap-up.

---

# Revision System

To make sure tasks don't get stuck in a loop forever burning through API credits, I put a strict limit on revisions (`MAX_REVISIONS = 2`).

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

If the Evaluator asks for revisions more than 2 times, the workflow stops retrying and automatically surfaces the current best output to the human review step so you can decide what to do.

---

# Stateful Workflow

LangGraph passes a shared `AgentState` dictionary from node to node throughout the whole run.

Here is what's inside the state:

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

Because every node updates this state dictionary, agents always know what previous workers did without losing context.

---

# Persistence

Everything in AgentSwarm is backed by **PostgreSQL**. I used SQLAlchemy for the application tables and LangGraph's official `PostgresSaver` for graph checkpoints.

Saved information includes:

* User accounts & hashed passwords
* Tasks and their real-time statuses
* Generated plans, research, code, and content
* Evaluator reviews and human feedback history
* Final answers
* Share tokens and file paths

If your server restarts or a worker finishes a step, the entire workflow can be resumed right from the last checkpoint.

---

# Artifact System

When the coder writes files, I don't just dump them into a database string. They get written as actual files inside an artifacts folder:

```text
artifacts/
└── generated/
    └── <task_id>/
        ├── task_<id>_code.txt
        └── task_<id>_revision_<n>_code.txt
```

My artifact manager helper handles:

* Keeping files neatly grouped by task ID
* Sanitizing filenames so nobody can do path traversal tricks (`../`)
* Setting a 5 MB file size limit so disks don't fill up
* Listing and serving files securely through FastAPI's `FileResponse`
* Deleting files when a user deletes their task

---

# Authentication & BYOK

I built full JWT-based authentication for the app:

* Signup and login with email & password
* 60-minute JWT bearer tokens stored in localStorage
* Password resets with expiring tokens sent via email
* Optional Google Sign-In using Google Identity Services (OAuth JWTs)
* **Bring Your Own Key (BYOK)**: If shared server credits run low, users can click the key icon in the dashboard and save their personal Gemini, Groq, or Tavily keys. The backend masks the keys (`••••••••`) and uses them for that user's tasks.

Every task endpoint checks `task.user_id == current_user.id`, so users can never see or modify each other's tasks.

---

# Task Management

From the dashboard, you can:

* Type a new goal and watch agents run in real time
* See the live status change (Planning, Coding, Evaluating, etc.)
* Click "Stop Task" if you change your mind mid-run
* Review the evaluator's critique
* Approve or send back revisions with custom notes
* Preview and download generated code artifacts
* Generate a public share link for completed tasks
* Delete finished or stopped tasks from your history

---

# Task States

Tasks move through a well-defined state machine:

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
   │       FINALIZING   │
   │          │         │
   └──────────┼─────────┘
              │
              ▼
          COMPLETED
```

Terminal states include:

```text
COMPLETED
FAILED
STOPPED
EVALUATION_UNAVAILABLE
```

I added a database guard (`UPDATE tasks WHERE status != 'STOPPED'`) so that if a user clicks Stop, any late background worker response gets safely dropped instead of accidentally flipping the task back to running.

---

# External Services

## Groq
Runs the primary workers (Planner, Coder, Content, Finalizer) using `openai/gpt-oss-120b`. Groq's inference speeds make multi-step agent interactions feel responsive instead of taking minutes.

## Google Gemini
Runs the Evaluator using `gemini-3.6-flash`. Using a different LLM family prevents the evaluator from having the exact same blind spots as the coder.

## Tavily
Used by the Researcher agent. Unlike standard search APIs that return messy HTML or ad links, Tavily returns clean markdown summaries ready for LLMs to read.

---

# RAG Knowledge Base

I set up a local ChromaDB vector store in `rag/` to give the Evaluator extra context. 

Reference guidelines and documentation are chunked into 500-character segments with 100-character overlap. When checking a piece of code, the evaluator pulls relevant reference chunks to compare against ground truth standards before deciding on a verdict.

---

# Handling Quota & API Errors

External APIs can occasionally fail due to rate limits (HTTP 429) or temporary outages (503). 

Instead of crashing the backend or falsely passing unverified code, AgentSwarm catches these errors and marks the task as:

```text
EVALUATION_UNAVAILABLE
```

The UI displays an informative alert explaining that the evaluator quota was reached, so you know the code wasn't verified rather than thinking it passed inspection.

---

# API Endpoints

| Method   | Endpoint                           | What it does           |
| -------- | ---------------------------------- | ---------------------- |
| `GET`    | `/health`                          | Quick health check     |
| `POST`   | `/auth/signup`                     | Register a new account |
| `POST`   | `/auth/login`                      | Login and get JWT      |
| `POST`   | `/auth/google`                     | Google OAuth login     |
| `GET`    | `/auth/api-keys`                   | View configured keys   |
| `POST`   | `/auth/api-keys`                   | Save personal API keys |
| `POST`   | `/auth/forgot-password`            | Request reset email    |
| `POST`   | `/auth/reset-password`             | Set new password       |
| `GET`    | `/auth/me`                         | Get current user info  |
| `PATCH`  | `/auth/profile`                    | Update profile name    |
| `DELETE` | `/auth/account`                    | Delete account & data  |
| `POST`   | `/tasks`                           | Submit a new task      |
| `GET`    | `/tasks`                           | List your task history |
| `GET`    | `/tasks/{id}`                      | Get single task status |
| `POST`   | `/tasks/{id}/stop`                 | Stop a running task    |
| `POST`   | `/tasks/{id}/approval`             | Approve or reject task |
| `GET`    | `/tasks/{id}/artifacts`            | List task files        |
| `GET`    | `/tasks/{id}/artifacts/{filename}` | Download a file        |
| `POST`   | `/tasks/{id}/share`                | Create share link      |
| `GET`    | `/share/{token}`                   | View public task       |
| `DELETE` | `/tasks/{id}`                      | Delete a task          |

FastAPI automatically serves interactive Swagger docs at:
```text
http://localhost:8000/docs
```

---

# Tech Stack

| Part            | Technology                   |
| --------------- | ---------------------------- |
| Frontend        | React 19, Vite, Lucide Icons |
| Styling         | Custom Vanilla CSS           |
| Backend         | Python 3.11+, FastAPI        |
| Server          | Uvicorn                      |
| Orchestration   | LangGraph, LangChain         |
| Primary LLM     | Groq `openai/gpt-oss-120b`   |
| Evaluator LLM   | Gemini `gemini-3.6-flash`    |
| Web Search      | Tavily API                   |
| Database        | PostgreSQL with SQLAlchemy   |
| Checkpointing   | Psycopg3 + PostgresSaver     |
| Data Validation | Pydantic v2                  |
| Auth            | JWT + Passlib / Bcrypt       |
| Vector Store    | ChromaDB                     |

---

# Project Structure

```text
AgentSwarm/
├── agents/             # Worker code (planner, coder, researcher, content, evaluator, finalizer)
├── api/                # FastAPI app, route handlers, and Pydantic schemas
├── artifacts/          # Local file manager for saving and downloading code files
├── auth/               # Password hashing, JWT dependencies, and auth routes
├── database/           # SQLAlchemy database models and connection engine
├── frontend/           # React single-page app
│   ├── src/
│   │   ├── components/ # Modals (API keys, name prompt, Google button)
│   │   ├── pages/      # Dashboard, Login, Signup, ResetPassword, SharedTask
│   │   └── config.js   # API URL configuration
├── graph/              # LangGraph workflow, nodes, shared state, and approval interrupts
├── rag/                # Document chunker, embedding search, and ChromaDB helpers
├── services/           # Status transitions, background task runner, and email sender
├── tests/              # Pytest test suite covering all APIs and graph logic
├── main.py             # Simple CLI runner for testing locally
└── requirements.txt    # Python dependencies
```

---

# Setting Up Locally

### 1. Prerequisites
Make sure you have:
- Python 3.11 or newer
- Node.js (v18+) and npm
- PostgreSQL running locally or a free database from Neon or Supabase

### 2. Clone the repo
```bash
git clone https://github.com/suhas-2007/AgentSwarm.git
cd AgentSwarm
```

### 3. Setup Python virtual environment
```powershell
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On Linux or Mac
python3 -m venv venv
source venv/bin/activate
```

Install backend packages:
```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file
Make a copy of `.env.example`:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
DATABASE_URL=postgresql://postgres:password@localhost:5432/agentswarm
JWT_SECRET_KEY=use_a_long_random_secret_string
FRONTEND_URL=http://localhost:5173
```

### 5. Start the backend
```powershell
python -m uvicorn api.api:app --reload --port 8000
```
FastAPI will start up at `http://127.0.0.1:8000`. You can test it by going to `http://127.0.0.1:8000/health`.

### 6. Start the frontend
Open a second terminal window:

```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

# Automated Tests

I put together a test suite with 64 automated tests covering all edge cases, workflow routes, and security checks.

### Running the tests

```powershell
# Set PYTHONPATH to project root and run pytest
$env:PYTHONPATH = "."
pytest -v
```

### What the tests cover

| Test File | What it checks | Tests |
| :--- | :--- | :--- |
| `test_workflow_routing.py` | Checks that tasks route properly to researcher, coder, or content, and handles PASS/REVISE verdicts | 13 |
| `test_workflow_edge_cases.py` | Tests worker error handling, user stop safeguards, and evaluator fallback states | 8 |
| `test_security_api.py` | Makes sure users can't access each other's tasks, tests share token sanitization, and checks password strength | 6 |
| `test_task_approval_api.py` | Tests human approval flow and verifies that rejections require non-empty feedback | 3 |
| `test_revision_limit.py`, `test_revision.py` | Makes sure revisions stop after 2 tries and don't loop forever | 3 |
| `test_task_sync.py` | Tests syncing state between LangGraph and PostgreSQL without overwriting stopped tasks | 5 |
| `test_planner.py` | Verifies the planner decomposes prompts into valid subtasks and rejects invalid agents | 7 |
| `test_rag.py` | Tests sentence chunking, ChromaDB vector queries, and metadata preservation | 4 |
| `test_tasks_api.py`, `test_tasks_workflow_api.py` | Tests the REST endpoints, background runner, and lifecycle transitions | 5 |
| `test_checkpoint.py`, `test_checkpoint_persistence.py` | Verifies LangGraph's PostgreSQL checkpointer and state resumption | 3 |
| `test_full_workflow.py`, `test_full_revision.py` | End-to-end multi-step runs from user prompt all the way to finalizer | 10 |

---

# Step-by-Step Workflow Scenarios

Here are 3 actual walkthroughs showing how different prompts execute:

### Scenario 1: Straightforward Coding Task

**Prompt**: *"Write an efficient Python function to detect cycles in a directed graph using Kahn's topological sort."*

```text
[1. START]      You submit the prompt in the dashboard
                 └── Task #101 created with status: STARTING
[2. PLANNER]    Planner generates a 1-step plan:
                 └── Task 1: "coder" - Implement Kahn's cycle detection algorithm
[3. WORKER]     Coder generates Python code with edge case checks and docstrings
                 └── File saved to artifacts/generated/101/task_101_code.txt
                 └── Status moves from CODING to EVALUATING
[4. EVALUATOR]  Gemini checks the code for logic errors, time complexity O(V+E), and formatting:
                 └── Evaluator outputs: "VERDICT: PASS - Kahn's algorithm correctly tracks in-degrees"
                 └── Status moves from EVALUATING to WAITING_FOR_HUMAN
[5. REVIEW]     You review the code in the dashboard and click "Approve & Finalize"
                 └── Backend receives: POST /tasks/101/approval {"approved": true}
[6. FINALIZER]  Finalizer prepares the markdown explanation and marks the task COMPLETED
```

---

### Scenario 2: Research with Human Feedback & Revision

**Prompt**: *"Research quantum computing breakthroughs in 2024 and write an executive summary for non-technical leadership."*

```text
[1. START]      You submit the prompt
[2. PLANNER]    Planner creates two tasks:
                 └── Task 1: "researcher" - Query Tavily for 2024 quantum announcements
                 └── Task 2: "content" - Draft executive summary using research findings
[3. RESEARCHER] Queries Tavily for neutral atom and fault-tolerant quantum milestones
                 └── Gathers findings into shared workflow state
[4. CONTENT]    Writes the initial executive summary draft
[5. EVALUATOR]  Gemini reviews facts and confirms accuracy: "VERDICT: PASS"
                 └── Status moves to WAITING_FOR_HUMAN
[6. REVIEW]     You read the draft but want to know more about commercial timelines:
                 └── You type: "Include estimated commercial timeline and market impact"
                 └── You click "Ask for changes" (Reject)
                 └── Status moves to REVISING (Revision count: 1/2)
[7. REVISION]   Content worker runs again with your notes:
                 └── Adds dedicated sections covering 2028-2030 commercial estimates
[8. EVALUATOR]  Gemini checks the updated draft: "VERDICT: PASS"
[9. REVIEW]     You review the updated version and click "Approve & Finalize"
[10. FINALIZER] Final answer assembled and displayed. Status: COMPLETED.
```

---

### Scenario 3: Stopping a Task Mid-Run

**Prompt**: *"Generate a comprehensive 100-page market analysis of renewable energy in South America."*

```text
[1. START]      You submit the prompt
[2. RUNNING]    Planner creates tasks and Researcher starts making web queries
[3. USER STOP]  You realize the prompt is too broad and click "Stop Task" on the dashboard
                 └── API calls: POST /tasks/105/stop
                 └── Postgres updates Task #105: status = "STOPPED", current_task_id = null
[4. GUARD]      When the background thread finishes its current step and calls sync:
                 └── Query runs: UPDATE tasks WHERE id=105 AND status != 'STOPPED'
                 └── 0 rows affected: the STOPPED status is never overwritten!
[5. CLEANUP]    Task stays STOPPED cleanly without corrupting state or leaving ghost processes.
```

---

# Security & Data Isolation

Here are the safety checks I implemented across the application:

* **User task isolation**: Every private route verifies `task.user_id == current_user.id`. If someone tries guessing another user's task ID in the URL, they get a clean `404 Not Found` so they cannot even know if that task exists.
* **Sanitized share tokens**: Public sharing (`/share/{token}`) only works for tasks in `COMPLETED` status. If someone tries sharing a running or failed task, they get a 403. Also, shared responses strip out user IDs, emails, and internal state.
* **Password policy**: Enforces at least 8 characters, hashes passwords with bcrypt, and reset tokens expire after 15 minutes.
* **Path traversal prevention**: Filenames are validated with strict regex patterns before any file write. Traversal patterns like `../` or absolute paths are blocked immediately.

---

# Production Deployment Notes

### Environment Template
Create `.env` using your real server credentials:

```powershell
copy .env.example .env
```

Make sure you never commit `.env` into git.

### Dockerfile
If you want to package the backend with Docker:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

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

### PostgreSQL Setup
Create your database and user:

```sql
CREATE DATABASE agentswarm;
CREATE USER agentswarm_user WITH ENCRYPTED PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE agentswarm TO agentswarm_user;
```

Update your `.env` connection string:
```env
DATABASE_URL=postgresql://agentswarm_user:your_password_here@localhost:5432/agentswarm
```

### Building the Frontend for Production
```bash
cd frontend
npm install
npm run build
```
This outputs production HTML, CSS, and JS inside `frontend/dist/` that can be served with Nginx, Render, Vercel, or Cloudflare Pages.

---

## License

MIT License

---

## Author

**Raavi Suhas**  
GitHub: [https://github.com/suhas-2007/AgentSwarm](https://github.com/suhas-2007/AgentSwarm)
