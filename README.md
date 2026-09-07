# AgentSwarm

## Multi-Agent Task Orchestration Engine

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

This allows each stage to focus on a specific responsibility.

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

# Testing

AgentSwarm includes local tests for core workflow infrastructure.

### Compile the Project

```powershell
.\venv\Scripts\python.exe -m compileall .
```

### Artifact Tests

```powershell
.\venv\Scripts\python.exe -m tests.test_artifacts_local
```

Tests artifact creation, validation, security checks, and deletion.

### Workflow Routing Tests

```powershell
.\venv\Scripts\python.exe -m tests.test_workflow_routing
```

Tests:

* Worker routing
* Evaluator PASS routing
* Evaluator REVISE routing
* Revision limits
* Evaluator-unavailable routing
* Human approval
* Human rejection

### Task Synchronization Tests

```powershell
.\venv\Scripts\python.exe -m tests.test_task_sync
```

Tests:

* Normal synchronization
* Completed tasks
* Evaluator-unavailable state
* STOPPED state protection
* Partial state preservation

---

# Security

AgentSwarm includes several application-level security controls.

### Authentication

JWT authentication protects user-specific operations.

### Authorization

Users can only access tasks that belong to their account.

### Input Validation

API requests are validated using Pydantic.

### Artifact Isolation

Artifacts are stored inside task-specific directories.

### Path Traversal Protection

Artifact filenames reject unsafe paths and path separators.

### Artifact Size Limits

Artifacts are limited to a maximum allowed size.

### Secure Sharing

Task share tokens use cryptographically secure random generation.

### Secret Management

API keys and secrets are supplied through environment variables.

---

# Reliability

AgentSwarm includes safeguards for long-running and multi-stage workflows.

### Bounded Revisions

Revision loops have a maximum number of attempts.

### Terminal State Protection

Stopped and terminal tasks are protected from incorrect state overwrites.

### Persistent Checkpoints

LangGraph workflow state is persisted through PostgreSQL.

### Evaluator Failure Handling

Evaluator quota and rate-limit failures are represented explicitly as:

```text
EVALUATION_UNAVAILABLE
```

rather than being treated as successful evaluations.

### Background Execution

Task execution is separated from the initial API request through the task runner.

---

# Example

A user submits:

```text
Research a graph algorithm, implement it in Python,
and explain its complexity.
```

AgentSwarm can produce a workflow similar to:

```text
                    User Request
                         │
                         ▼
                      Planner
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Researcher       Coder         Content
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                     Evaluator
                         │
                    ┌────┴────┐
                    │         │
                  PASS      REVISE
                    │         │
                    ▼         ▼
              Human Review  Worker
                    │
              ┌─────┴─────┐
              │           │
           APPROVE       REJECT
              │           │
              ▼           │
          Finalizer       │
              │           │
              ▼           │
         Final Output ◄────┘
```

The exact task decomposition depends on the user's request.

---

# Design Principles

### Specialized Agents

Each agent has a focused responsibility instead of one model performing every operation.

### Explicit Workflow State

Agent communication occurs through structured LangGraph state.

### Independent Evaluation

The Evaluator is separated from the primary worker model.

### Controlled Autonomy

Revision attempts are bounded.

### Human Oversight

Human approval can be required before finalization.

### Persistent Execution

Workflow state is checkpointed through PostgreSQL.

### Secure Resource Management

Authentication, authorization, artifact security, and secret management are built into the application.

---

# Current Status

* [x] Multi-agent planning
* [x] Research agent
* [x] Coding agent
* [x] Content agent
* [x] Independent evaluator
* [x] Automatic revision loop
* [x] Human-in-the-loop approval
* [x] LangGraph orchestration
* [x] PostgreSQL checkpointing
* [x] JWT authentication
* [x] User task authorization
* [x] Task stopping
* [x] Task deletion
* [x] Artifact generation
* [x] Artifact downloads
* [x] Secure task sharing
* [x] Frontend workflow visualization
* [x] Evaluator quota handling
* [x] Artifact security tests
* [x] Workflow routing tests
* [x] Task synchronization tests

---

# Future Improvements

Potential improvements include:

* Parallel execution of independent tasks
* Additional specialized agents
* Streaming agent execution
* Rich artifact formats
* Distributed task workers
* Advanced observability and tracing
* More sophisticated dependency scheduling
* Improved evaluation strategies
* Production deployment infrastructure

---

# License

MIT License

---

## Author

**Raavi Suhas**

GitHub: [https://github.com/suhas-2007/AgentSwarm](https://github.com/suhas-2007/AgentSwarm)
