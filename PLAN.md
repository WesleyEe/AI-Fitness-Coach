# Sprint Roadmap

Each sprint = one reviewable increment. We stop after each one for your review before continuing. See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design these sprints build toward.

| Sprint | Theme | Key learning |
|---|---|---|
| 1 | Project foundation | Service architecture, containerization, backend/frontend wiring |
| 2 | Fitness data management | DB schema design, CRUD APIs, ORM |
| 3 | Basic LLM integration | LLM app architecture, prompt engineering |
| 4 | RAG system | Embeddings, vector search, retrieval pipelines |
| 5 | LangGraph agent | Agent architecture, state machines, tool calling |
| 6 | Personalized coaching intelligence | Multi-source reasoning, follow-up questioning |
| 7 | Kubernetes deployment | Cloud-native concepts, manifests, Helm |

---

## Sprint 1: Project Foundation

**Goal:** A running skeleton — empty but real, end to end. Prove the wiring works before any feature logic exists.

**Architecture for this sprint:**
Three containers via Docker Compose: `postgres` (empty DB, just proving connectivity), `backend` (FastAPI with a `/health` endpoint that also checks DB connectivity), `frontend` (React app with one page that calls `/health` and displays status). No business logic yet — this sprint is purely about the scaffolding and the seams between services.

**Implementation tasks:**
1. Repo structure: `backend/`, `frontend/`, `infra/` (or `docker-compose.yml` at root — your call, I'll ask).
2. `backend`: FastAPI app, `pydantic-settings` config, SQLAlchemy engine pointed at Postgres, `GET /health` returning `{status, db_connected}`.
3. `frontend`: Minimal Vite + React app, one page fetching `/health` and rendering the result — proves CORS/networking is correct.
4. `docker-compose.yml`: three services, a named volume for Postgres data, `.env.example` for config, sensible service dependencies (`depends_on` + a DB healthcheck).
5. `README` section: how to run it (`docker compose up`), what you should see.

**Testing:**
- `docker compose up` brings up all three services cleanly.
- Backend `/health` returns 200 with `db_connected: true`.
- Frontend loads and displays the health status fetched from the backend.
- One basic backend test (e.g. via `pytest` + `httpx` TestClient) hitting `/health`.

**Learning objectives:**
- Why a reverse-proxy-free dev setup works differently from production (CORS, ports, service DNS names inside Compose).
- Why we check DB connectivity in `/health` rather than just returning a static 200 — health checks should verify real dependencies.
- Docker Compose networking basics: service name resolution, `depends_on` vs. actual readiness.

**Possible future improvements (not now):** structured logging, request tracing, a proper `/health` vs `/ready` split (relevant again in Sprint 7 for K8s probes).

**Decisions locked in:**
- Repo layout: flat (`backend/`, `frontend/`, `docker-compose.yml` at project root).
- Python tooling: `uv`.
- LLM provider (used from Sprint 3 onward): locally hosted **Qwen via Ollama** — no API keys, fully offline. Note for Sprint 3/Compose: since Ollama already runs on the host, the backend container will need to reach it via `host.docker.internal` (or a Compose Ollama service, decided when we get there) rather than `localhost`.

---

## Sprint 2: Fitness Data Management (preview only — detailed at sprint start)

Schema for users, workouts, sport-specific sessions (football/Hyrox/running), injuries. CRUD APIs. No AI yet — this is "boring but essential" backend work that everything else depends on.

## Sprint 3: Basic LLM Integration (preview only)

Chat endpoint, single LLM call (no agent, no tools yet), simple conversation state. Goal: understand raw LLM API mechanics before adding orchestration complexity.

## Sprint 4: RAG System (preview only)

Ingest a small curated set of docs per domain, chunk + embed + store in pgvector, build a retriever, test retrieval quality manually before wiring into anything else.

## Sprint 5: LangGraph Agent (preview only)

Replace the single LLM call with a LangGraph graph: intent analysis → tool routing (DB tool / RAG tool) → reasoning → recommendation.

## Sprint 6: Personalized Coaching Intelligence (preview only)

Deepen the reasoning node to cross-reference injury history, training history, and retrieved guidance; add clarification loops when data is missing.

## Sprint 7: Kubernetes Deployment (preview only)

Production-shaped container images, K8s manifests, Helm chart, secrets management, decide together on local (kind/minikube) vs. cloud target.

---

Later sprints will get this same level of detail (goal, architecture, tasks, testing, learning objectives, future improvements) when we get there — not before, so decisions reflect what we actually learned in prior sprints rather than upfront guessing.
