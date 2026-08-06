from fastapi import APIRouter

from app.core.db import check_db_connection

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "db_connected": check_db_connection(),
    }
