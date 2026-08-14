# Architecture Proposal

## 1. Guiding principles

- **Learning over polish.** Every architectural choice should be explainable, not just "best practice by default." We pick boring, well-documented tools so the focus stays on the concepts (agents, RAG, orchestration), not on fighting infrastructure.
- **Incremental complexity.** Sprint 1 has no LLM at all. Sprint 3 has an LLM but no agent. Sprint 5 has an agent but no personalization depth. We only add one new hard concept per sprint.
- **Each sprint is runnable.** `docker compose up` should always produce something you can click through or curl, from Sprint 1 onward.

## 2. High-level system

```
                        ┌─────────────────────┐
                        │   React Frontend     │
                        │  (chat + data views)  │
                        └──────────┬───────────┘
                                   │ REST / SSE
                        ┌──────────▼───────────┐
                        │     FastAPI Backend   │
                        │                       │
                        │  ┌─────────────────┐  │
                        │  │  LangGraph Agent │  │
                        │  │                 │  │
                        │  │  Intent → Plan  │  │
                        │  │  → Tools → Answer│  │
                        │  └───┬─────────┬───┘  │
                        └──────┼─────────┼───────┘
                               │         │
                 ┌─────────────▼───┐  ┌──▼──────────────┐
                 │   PostgreSQL     │  │  PostgreSQL +    │
                 │  (structured:    │  │  pgvector         │
                 │  users, workouts,│  │  (RAG knowledge   │
                 │  sports, injury) │  │  base embeddings) │
                 └──────────────────┘  └──────────────────┘
```

We use **one PostgreSQL instance with two concerns** (structured relational tables + a `pgvector` extension for embeddings) rather than a separate vector DB. This is a deliberate simplification: fewer moving parts, one connection pool, one backup story — and it's realistic for a project at this scale. A dedicated vector DB (Pinecone, Qdrant, Weaviate) is a reasonable future improvement to explore once RAG scale/perf becomes the learning goal, but not before.

## 3. Backend structure (target shape by Sprint 5, not built yet)

```
backend/
  app/
    main.py                # FastAPI app entrypoint
    core/
      config.py             # settings via pydantic-settings
      db.py                 # SQLAlchemy engine/session
    models/                 # SQLAlchemy ORM models
    schemas/                # Pydantic request/response schemas
    api/
      routes/
        health.py
        users.py
        workouts.py
        chat.py
    agent/
      graph.py               # LangGraph graph definition
      nodes/                 # intent, reasoning, recommendation nodes
      tools/                 # db_query_tool, rag_search_tool
    rag/
      ingest.py
      retriever.py
  tests/
  Dockerfile
  requirements.txt

frontend/
  (React app — chat UI + simple data views)
  Dockerfile

infra/
  docker-compose.yml
  k8s/                      # added in Sprint 7
    helm/
```

We won't create most of this in Sprint 1 — only what Sprint 1 needs. This tree is here so you can see where things are headed.

## 4. Technology choices and why

| Concern | Choice | Why |
|---|---|---|
| Backend framework | FastAPI | Async-native, auto OpenAPI docs, strong typing via Pydantic — good for learning clean API design |
| ORM | SQLAlchemy 2.0 (+ Alembic for migrations) | Industry standard, teaches real schema evolution instead of hand-written SQL only |
| Database | PostgreSQL | Relational integrity for structured fitness data; `pgvector` extension covers RAG without a second system |
| Agent orchestration | LangGraph | Explicit state machine model — better for learning *how* agent control flow works than a black-box agent framework |
| LLM access | LangChain's model wrappers, backed by **Ollama running a local Qwen model** | No API keys/cost while learning; fully local and offline-capable. LangChain's abstraction still means we could swap to a hosted provider later with minimal code change |
| Frontend | React (Vite, plain fetch/SSE, no heavy state library at first) | Keep it minimal; the frontend is a viewport onto the agent, not the learning focus |
| Containerization | Docker Compose (Sprints 1–6), Kubernetes + Helm (Sprint 7+) | Compose is the right complexity level until we intentionally study cloud-native deployment |

## 5. Data model (conceptual, refined in Sprint 2)

Core entities:
- `users` — profile, goals, sports played, preferences
- `workouts` — generic entry (date, type, sets/reps/weight/duration/distance/pace/HR/calories/notes)
- `football_sessions` — position, match duration, intensity, performance notes, injuries flagged
- `hyrox_sessions` — station-by-station times (ski erg, sled push/pull, burpees, row, farmers carry, lunges, wall balls)
- `running_sessions` — distance, pace, VO2max estimate, HR zones
- `injuries` — type, date, severity, recovery exercises, restrictions, linked to affected workouts

Design stance: one `workouts` table for generic logging + **sport-specific detail tables** joined by `workout_id`, rather than one giant sparse table. This is extensible (new sports = new detail table) and keeps queries clean. We'll finalize this in Sprint 2 with your input.

## 6. RAG knowledge base (Sprint 4)

- Source documents organized by domain: `football/`, `hyrox/`, `bodybuilding/`, `injury_prevention/`.
- Chunked, embedded, stored in `pgvector`.
- Retrieval is domain-filtered where possible (e.g., a Hyrox question searches the Hyrox namespace first) to reduce noise before falling back to full-corpus search.

## 7. Agent design (Sprint 5–6)

LangGraph state machine, roughly:

```
START → intent_analysis → route:
    needs_personal_data?  → db_query_tool
    needs_expert_knowledge? → rag_search_tool
    needs_both? → both, then merge
  → reasoning_node (combines structured + retrieved context)
  → recommendation_node (produces personalized advice)
  → END (or → clarification_node if info is missing, looping back)
```

Key learning point: the agent's "tools" are just the Sprint 2 CRUD APIs and the Sprint 4 RAG retriever, called internally rather than over HTTP. Nothing new is invented here — Sprint 5 is about *orchestrating* what already exists.

## 8. Deployment path

- **Sprints 1–6:** Docker Compose — `postgres`, `backend`, `frontend` services, one `.env`.
- **Sprint 7:** containerize properly for K8s (multi-stage builds, non-root users, health/readiness probes), write manifests, then Helm chart, then discuss GitOps (Argo CD / Flux) conceptually.

## 9. What we are deliberately NOT doing early

- No auth/multi-user system until it's needed (Sprint 1–5 assume a single default user).
- No streaming UI polish until the chat mechanics work.
- No microservices split — one backend service throughout Compose sprints.
- No managed cloud DB/hosting — everything local until the Kubernetes sprint, and even then targeting local K8s (kind/minikube) rather than a cloud bill, by design.
