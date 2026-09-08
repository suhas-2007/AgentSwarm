# AgentSwarm Cloud Deployment Guide

This guide walks you through deploying **AgentSwarm** (React Frontend + FastAPI Backend + Managed PostgreSQL + LangGraph Checkpointer) to **Render** or **Railway**.

---

## Architecture in Production

```text
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                    │
│           Hosted as a Static Site (e.g. on Render)          │
│           https://agentswarm-web.onrender.com               │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS API Calls (Bearer JWT)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend API                     │
│         Hosted as a Web Service (Python 3.11 / Uvicorn)     │
│           https://agentswarm-api.onrender.com               │
└──────────────────────────────┬──────────────────────────────┘
                               │ TCP / SSL Connection
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Managed PostgreSQL Database                │
│            Application State & LangGraph Checkpointer       │
└─────────────────────────────────────────────────────────────┘
```

---

## Option A: 1-Click Blueprint Deployment on Render (Recommended)

Render provides built-in support for Infrastructure-as-Code via [`render.yaml`](./render.yaml). This will automatically provision the PostgreSQL database, the FastAPI backend, and the React frontend simultaneously.

### Step 1: Push Code to GitHub
Ensure all code has been pushed to your repository:
```bash
git push origin main
```

### Step 2: Create a Blueprint on Render
1. Go to [dashboard.render.com](https://dashboard.render.com) and sign in.
2. Click the **"New +"** button in the top navigation and select **"Blueprint"**.
3. Select and connect your repository: `suhas-2007/AgentSwarm`.
4. Render will inspect `render.yaml` and display the resources to be created:
   * **Database**: `agentswarm-db` (PostgreSQL)
   * **Web Service**: `agentswarm-api` (FastAPI backend)
   * **Static Site**: `agentswarm-web` (React frontend)

### Step 3: Enter Your Secret Keys
Render will automatically link `DATABASE_URL` and generate a secure `JWT_SECRET_KEY`. It will prompt you to provide your third-party API keys:
* `GEMINI_API_KEY`: Your Google Gemini API Key
* `GROQ_API_KEY`: Your Groq Cloud API Key
* `TAVILY_API_KEY`: Your Tavily Search API Key

*(Optional: configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM` if you want password reset emails).*

### Step 4: Click "Apply"
Render will:
1. Provision the managed PostgreSQL database.
2. Build and start the FastAPI service with Uvicorn.
3. Build the React frontend with Vite, automatically wiring `VITE_API_URL` to point to the backend service.
4. Set up SPA client-side routing so direct links like `/dashboard` or `/login` work seamlessly.

---

## Option B: Deploying on Railway

If you prefer using [railway.app](https://railway.app):

### Step 1: Provision PostgreSQL Database
1. Go to [railway.app/new](https://railway.app/new) and start a new project.
2. Click **"Provision PostgreSQL"**.
3. Once created, click the PostgreSQL service, go to **Variables**, and note the `DATABASE_URL`.

### Step 2: Deploy FastAPI Backend
1. Click **"New Service"** $\rightarrow$ **"GitHub Repo"** $\rightarrow$ select `suhas-2007/AgentSwarm`.
2. In the service settings:
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn api.api:app --host 0.0.0.0 --port $PORT`
3. Under **Variables**, add:
   * `DATABASE_URL`: `${{Postgres.DATABASE_URL}}` (or reference the Postgres service)
   * `JWT_SECRET_KEY`: Generate a random 32+ character string
   * `GEMINI_API_KEY`: Your Gemini API Key
   * `GROQ_API_KEY`: Your Groq API Key
   * `TAVILY_API_KEY`: Your Tavily API Key
   * `ALLOWED_ORIGINS`: Comma-separated domains of your frontend
4. Under **Settings** $\rightarrow$ **Networking**, click **"Generate Domain"** (e.g. `https://agentswarm-backend.up.railway.app`).

### Step 3: Deploy React Frontend
1. Click **"New Service"** $\rightarrow$ **"GitHub Repo"** $\rightarrow$ select `suhas-2007/AgentSwarm`.
2. In the service settings:
   * **Root Directory**: `frontend`
   * **Build Command**: `npm install && npm run build`
   * **Start Command**: `npx serve -s dist -l $PORT` (or deploy as Static Site on Vercel)
3. Under **Variables**, add:
   * `VITE_API_URL`: The backend domain generated in Step 2 (e.g. `https://agentswarm-backend.up.railway.app`)
4. Under **Settings** $\rightarrow$ **Networking**, click **"Generate Domain"**.

---

## Post-Deployment Verification

### 1. Test Backend Health Check
Open your browser or run in terminal:
```bash
curl https://<your-backend-domain>/health
```
Expected response:
```json
{"status":"ok"}
```

### 2. Verify Interactive Documentation
Visit:
```text
https://<your-backend-domain>/docs
```
You should see the Swagger UI listing all auth, task, and artifact routes.

### 3. Verify Frontend Application
1. Open `https://<your-frontend-domain>/signup`
2. Create a new test user account.
3. Submit a goal (e.g. *"Write a Python script to calculate Fibonacci numbers"*).
4. Watch the live multi-agent DAG progress:
   $$\text{Planner} \longrightarrow \text{Coder} \longrightarrow \text{Evaluator} \longrightarrow \text{Human Review} \longrightarrow \text{Finalizer}$$
5. Approve and download the generated artifact file!

---

## Security & Maintenance Tips

* **Zero Secret Leakage**: Never commit `.env` files to git. All credentials must be set exclusively via your hosting provider's web dashboard.
* **CORS Protection**: The backend automatically allows origins matching `*.onrender.com` and `*.up.railway.app`, plus any URL configured in `FRONTEND_URL` or `ALLOWED_ORIGINS`.
* **Database Backups**: On Render and Railway, automated backups for PostgreSQL can be enabled in their respective database dashboard tabs.
