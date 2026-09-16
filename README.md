# SaaS Auth System — local setup

This project runs as a single FastAPI process on your machine. Docker, Redis,
and Celery have been removed:

- **No Redis** — API-key lookups, token checks, and rate limiting now query
  Postgres / run in-process (`core/rate_limit.py`) instead of a Redis cache.
- **No Celery** — verification emails are sent with FastAPI's built-in
  `BackgroundTasks` (`core/email.py`) instead of a separate Celery worker.
- **No Docker** — you run Postgres and the API directly on localhost.

## 1. Prerequisites

- Python 3.12+
- A local PostgreSQL server running on `localhost:5432`

Create the database once:

```bash
psql -U postgres -c "CREATE DATABASE auth;"
```

## 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Configure environment

`.env` already points at `postgresql+asyncpg://postgres:<password>@localhost:5432/auth`.
Update the password (and any other values) to match your local Postgres setup.

## 4. Run migrations

```bash
alembic upgrade head
```

## 5. Start the API

```bash
uvicorn main:app --reload
```

The API is now available at `http://localhost:8000`, and `frontend.html` (open
it directly in a browser) already points its console at that same address.

## Notes on the removed pieces

- `core/rate_limit.py` keeps login rate-limit counters in an in-memory dict.
  This resets on restart and only works correctly with a single process/worker
  — fine for local development, but not a substitute for a shared store if
  you ever scale to multiple workers or instances.
- `core/email.py` sends verification emails via a plain function scheduled
  with `background_tasks.add_task(...)`. Unlike Celery, there's no retry
  queue or persistence across restarts — a failed send is just logged.
