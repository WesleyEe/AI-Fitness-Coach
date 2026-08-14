# Fitness Coach AI Assistant

A full-stack, agentic AI application: a personalized fitness coach that combines a
user's own workout/injury history with a retrieval-augmented expert knowledge base,
reasons over both through a LangGraph state machine, and asks for clarification
instead of guessing when it doesn't have enough to answer safely.

Built end-to-end — schema design, API, RAG pipeline, agent orchestration, test
suite, containerization, and a Kubernetes deployment (raw manifests + a Helm chart)
— as a demonstration of the modern AI-application stack, not just a model wrapped in
a chat box.

**Status:** feature-complete, all layers implemented and tested (Docker Compose and
Kubernetes deployments both verified working end to end).

## What this project shows

- **LLM orchestration beyond a single prompt.** A [LangGraph](backend/app/agent/graph.py)
  state machine with real conditional routing: an intent-classification step decides
  — per question, via structured LLM output, not a keyword rule — whether a query
  needs the user's personal history, expert reference material, both, or neither,
  before a separate reasoning step decides whether to answer or ask a clarifying
  question first.
- **Retrieval-augmented generation, done properly.** Markdown knowledge base →
  heading-aware chunking → `pgvector`-backed embedding search (HNSW index, cosine
  similarity) → context injection, with a dedicated `/rag/search` endpoint for
  inspecting retrieval quality independent of the chat flow.
- **Real database design.** Structured, normalized schema (a generic `workouts`
  table plus sport-specific detail tables joined by `workout_id`, rather than one
  wide sparse table), managed with Alembic migrations from day one.
- **Production-shaped containers, not dev-only ones.** Multi-stage, non-root
  Docker images; a separate `/health` (readiness) vs `/live` (liveness) split;
  migrations run as a one-off Job/service rather than baked into the app's startup
  command, so they're safe under multiple replicas.
- **Kubernetes deployment, two ways.** Raw manifests (`infra/k8s/`) and an
  equivalent Helm chart (`infra/helm/`) — `StatefulSet` + PVC for Postgres,
  `Deployment` + `Service` for the stateless API/frontend, resource limits and
  probes throughout, migration ordering handled via a Helm post-install hook with
  a readiness-polling init container.
- **A real test suite.** 50 backend tests — route tests, node-level agent tests,
  full-graph integration tests, and DB-backed tests against real Postgres (not
  SQLite) where the schema uses Postgres-native types — plus routing logic tested
  as pure functions, independent of any LLM call.
- **Honest evaluation of the model, not just the plumbing.** Manual verification
  went past "does it respond" to inspecting intermediate agent state directly,
  which surfaced a genuine finding: the local 3B model can state specific facts
  that contradict its own retrieved context, with correct retrieval, correct DB
  queries, and correct prompting upstream. That distinction — and how to catch it
  — is documented in [PLAN.md](PLAN.md)'s Sprint 6 writeup, along with the rest of
  the engineering decisions made throughout the build.

## Architecture

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

One PostgreSQL instance covers both structured relational data and vector search
(via the `pgvector` extension) — a deliberate simplification over running a separate
vector database, sized appropriately for this project's scale. Full rationale and
the complete data model are in [ARCHITECTURE.md](ARCHITECTURE.md).

The agent graph itself:

```
START → classify_intent → [conditional] → fetch_context → reason → [conditional] → recommend → END
                        ↘ nothing needed ────────────────↗        ↘ ask_clarification → END
```

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic |
| Agent orchestration | LangGraph — explicit state machine, structured output, conditional routing |
| LLM / embeddings | LangChain model wrappers over a local Ollama runtime (Qwen + nomic-embed-text) |
| Data | PostgreSQL + `pgvector` (HNSW index, cosine similarity) |
| Frontend | React (Vite) |
| Testing | pytest, real Postgres for DB-dependent tests, mocked LLM calls for deterministic unit tests |
| Containerization | Docker / Docker Compose |
| Orchestration | Kubernetes — raw manifests and a Helm chart, `StatefulSet` + `Deployment` + `Job`, readiness/liveness probes |

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Then open http://localhost:5173. Full setup (Ollama models, knowledge base
ingestion, Kubernetes deployment) is in [DEPLOYMENT.md](DEPLOYMENT.md).

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — system design, technology choices and why,
  data model
- [PLAN.md](PLAN.md) — the full engineering log: every stage's goal, architecture,
  implementation, testing, and what was learned building it
- [DEPLOYMENT.md](DEPLOYMENT.md) — running the stack locally (Docker Compose) or on
  Kubernetes (raw manifests or Helm)
- [GITOPS.md](GITOPS.md) — what a GitOps rollout (Argo CD/Flux) would look like on
  top of the existing Helm chart, and why it isn't part of this project's scope

## A known, documented limitation

The local 3B model this project runs against can occasionally state specific facts
(an injury's status, a restriction) that contradict its own retrieved context, even
when retrieval, database queries, and prompt construction are all working correctly.
This isn't a plumbing bug — it's a real limit of a small local model's context
fidelity, caught by verifying intermediate agent state rather than trusting final
output, and it's the kind of thing a larger or hosted model would meaningfully
reduce. See [PLAN.md](PLAN.md)'s Sprint 6 section for the full investigation.
