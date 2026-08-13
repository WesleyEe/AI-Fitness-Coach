# --- builder: resolve and install dependencies into a venv ---
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# --- final: copy only the built venv + app code, run as non-root ---
FROM python:3.12-slim AS final

RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --create-home app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv ./.venv
COPY --chown=app:app app ./app
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic

ENV PATH="/app/.venv/bin:$PATH"
USER app

EXPOSE 8000

# Just serve - migrations are NOT run here. Baking "migrate then serve" into a
# single container's startup only works for exactly one instance; the moment
# you run more than one replica (Kubernetes Deployment, or even Compose scaled
# up), every instance would race to apply migrations concurrently on boot.
# Instead, whichever orchestrator is running this image decides when to run
# `alembic upgrade head` as a separate, one-off command against this same
# image - see docker-compose.yml's `migrate` service and infra/k8s's migration
# Job, both of which override this CMD rather than relying on it.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
