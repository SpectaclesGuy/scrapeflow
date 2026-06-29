# ScrapeFlow Context Service

ScrapeFlow Context Service is the long-chat memory and state-management backend for ScrapeFlow. It stores users, projects, conversations, audit messages, project context, and execution jobs, and it exposes a FastAPI API that downstream modules can consume.

The core design rule is that `project_context` is the source of truth. Raw `messages` are stored for audit, replay, debugging, and later summarization, but planner-style downstream consumers should work from `project_context` plus the latest user message instead of replaying the entire chat transcript.

## Architecture

- `app/main.py` wires the FastAPI app, routers, exception handling, and startup table creation.
- `app/models/` contains SQLAlchemy 2.x models for users, projects, conversations, messages, project context, and jobs.
- `app/schemas/` defines Pydantic v2 request and response models.
- `app/services/` contains domain logic, including automatic context creation and rule-based context updates from user messages.
- `app/routes/` contains REST endpoints.
- `alembic/` contains migration configuration and an initial schema revision.
- `tests/` contains pytest coverage for the main lifecycle flows.

## Setup

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
alembic revision --autogenerate -m "describe changes"
alembic upgrade head
```

## Run

```powershell
uvicorn app.main:app --reload
```

## API examples

Create a user:

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Mayank","email":"mayank@example.com"}'
```

Create a project:

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<user-id>","name":"Laptop Scraper"}'
```

Post a message and update context:

```bash
curl -X POST http://localhost:8000/conversations/<conversation-id>/messages \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"also include rating and ram and export as excel"}'
```

Read project context:

```bash
curl http://localhost:8000/projects/<project-id>/context
```

## Context-first behavior

When a message is posted, the service:

1. Stores the raw message for audit and replay.
2. Loads the linked conversation and project context.
3. Applies a temporary rule-based updater to extract URLs, domain, entity, fields, filters, and export format.
4. Persists the updated `project_context`.
5. Returns both the stored message and the latest context snapshot.

This keeps the system aligned with the long-chat requirement that context state stays compact, structured, and directly consumable by planner and execution modules.

## Future integrations

- Planner Agent can replace the temporary rule-based updater in `app/services/context_service.py`.
- Script Generator and Scraper can consume `project_context.current_plan`, `current_schema`, and job configuration.
- Validation and Evidence services can write structured outputs or confidence data into job results and context summaries.
- Export modules can use `export_format`, `fields`, and `filters` directly without replaying conversation history.
