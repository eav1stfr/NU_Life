# NU Life — Campus Club Events Platform (MVP)

Backend + minimal frontend for university club event publishing and
registration, built to survive high-concurrency registration bursts without
overselling capacity.

## Status

Stage 1 (project scaffolding) complete: FastAPI skeleton, Postgres, Redis,
Alembic, config, and a `/health` endpoint. No business logic yet — that lands
in later stages.

## Tech stack

- **Backend**: Python 3.12, FastAPI
- **Database**: PostgreSQL (via SQLAlchemy async + `asyncpg`)
- **Cache/queue**: Redis
- **Migrations**: Alembic (async template)
- **Dependency management**: [`uv`](https://docs.astral.sh/uv/)
- **Containerization**: Docker + docker-compose

## Project layout

```
app/
  api/           # routers (HTTP layer only)
  services/      # business logic, unit-testable independent of HTTP
  repositories/  # data access
  models/        # SQLAlchemy models
  config.py      # pydantic-settings, reads .env
  db.py          # async engine/session + Redis client factories
  main.py        # FastAPI app assembly
alembic/         # migrations, wired to app settings + Base.metadata
tests/
```

## Running with Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

This brings up Postgres, Redis, and the app, runs Alembic migrations, and
starts the API on `http://localhost:8000` with autoreload.

Check the stack is healthy:

```bash
curl http://localhost:8000/health
# {"status":"ok","database":true,"redis":true}
```

## Running locally without Docker

Requires a local Postgres and Redis (or point `.env` at ones you already
have running).

```bash
uv sync
cp .env.example .env
# edit .env: DATABASE_URL / REDIS_URL should point at localhost, e.g.
#   DATABASE_URL=postgresql+asyncpg://nu_life:nu_life@localhost:5432/nu_life
#   REDIS_URL=redis://localhost:6379/0
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Tests

```bash
uv run pytest
```

## Notes on the Docker setup

The `app` service bind-mounts the repo into the container for live reload,
but uses a separate named volume for `/app/.venv` so the container's
Linux-built virtualenv never overwrites the host's `.venv` (which may be
built for a different platform/interpreter).
