# Fitness Coach AI Assistant

A learning-focused project to build a personal AI fitness coach, incrementally, one Scrum-style sprint at a time — while deeply learning the modern AI application stack (agentic systems, LangGraph, RAG, PostgreSQL, FastAPI, Docker, Kubernetes).

Status: **Sprint 1 complete — foundation skeleton running end to end.**

See [PLAN.md](PLAN.md) for the full sprint roadmap and [ARCHITECTURE.md](ARCHITECTURE.md) for the system design.

## Ground rules for this project

- Build stage by stage. Do not skip ahead.
- Each sprint ends with a working, demoable increment.
- Explain *why* before writing *how*.
- Stop after each sprint for review before continuing.
- Git commits are handled by the user, not by Claude.

## Running Sprint 1

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173 — shows API status and DB connectivity
- Backend: http://localhost:8001/health — `{"status": "ok", "db_connected": true}`
- Backend interactive docs: http://localhost:8001/docs

Note: the backend and Postgres host ports are `8001` and `5434` (not the defaults `8000`/`5432`) because those were already bound by another local setup on this machine when Sprint 1 was built. Adjust `docker-compose.yml` / `.env` if that's not the case for you.

Backend tests (run locally, outside Docker):

```bash
cd backend
uv run pytest
```

Note: the Postgres image used is `pgvector/pgvector:pg16` — a drop-in Postgres 16 with the `pgvector` extension preinstalled. Sprint 1 doesn't use pgvector yet, but starting with this image now avoids a database image swap when Sprint 4 (RAG) needs it.
