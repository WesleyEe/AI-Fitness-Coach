from fastapi import APIRouter

from app.core.db import check_db_connection

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Readiness check: verifies the app can actually do its job (real DB
    connectivity), not just that the process is running. Used as Kubernetes'
    readinessProbe - if this fails, the pod is pulled out of Service load
    balancing until it passes again, but the container is NOT restarted.
    """
    return {
        "status": "ok",
        "db_connected": check_db_connection(),
    }


@router.get("/live")
def live() -> dict:
    """Liveness check: only confirms the process itself is up and responding -
    deliberately has NO external dependencies (no DB check). Used as Kubernetes'
    livenessProbe, which restarts the container on repeated failure. If this
    checked the DB like /health does, a brief Postgres blip would cause
    Kubernetes to kill and restart backend pods that were actually fine
    themselves - the wrong response to a problem that isn't in the process.
    This split was flagged as a gap back in Sprint 1's PLAN.md and left for
    exactly this sprint, where it actually matters.
    """
    return {"status": "ok"}
