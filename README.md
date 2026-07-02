# ScrapeFlow Context Service

ScrapeFlow Context Service is the backend memory and state-management backend for ScrapeFlow. It now also serves a complete vanilla-JS frontend for the Parse++ workflow.

## Frontend routes

The UI is served directly from FastAPI:

- `/` landing page
- `/login.html`
- `/signup.html`
- `/dashboard.html`
- `/projects.html`
- `/project.html`
- `/chat.html`
- `/context.html`
- `/plan.html`
- `/jobs.html`
- `/job.html`
- `/results.html`
- `/exports.html`
- `/settings.html`

Static frontend assets are served from `/ui/...`.

## Frontend structure

```text
app/ui/scrapeflow-ui/
  index.html
  login.html
  signup.html
  dashboard.html
  projects.html
  project.html
  chat.html
  context.html
  plan.html
  jobs.html
  job.html
  results.html
  exports.html
  settings.html
  css/
  js/
  assets/
```

## Backend setup

### Python version

This repo pins Python with `.python-version` and is configured for Python `3.11.11`.

### Virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
pip install -r requirements.txt
```

### Environment

```powershell
Copy-Item .env.example .env
```

### Database setup

Create a PostgreSQL database named `scrapeflow_context`, then ensure `DATABASE_URL` in `.env` points to it.

### Alembic migrations

```powershell
alembic upgrade head
```

## Run locally

```powershell
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/`.

## Mock mode

The frontend can fall back to realistic mock data when the backend is unavailable or the API surface is incomplete.

- Toggle it from the app top bar or Settings page.
- It is persisted in `localStorage` with the key `sf_use_mock`.

## Current real API coverage used by the UI

- users
- projects
- conversations
- messages
- project context
- jobs

The following product surfaces are mocked for now because matching backend endpoints are not yet implemented:

- login authentication
- results retrieval
- exports retrieval

## Deploy on Render

This repo is set up for Git-based Render deploys.

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Python version: `3.11.11`

If you are not using Render pre-deploy commands on your plan, run `alembic upgrade head` before deployment through your local machine, GitHub Actions, or a one-off job.
