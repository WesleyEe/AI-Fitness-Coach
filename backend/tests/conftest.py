import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.db import get_db
from app.main import app

# Tests run against the same Postgres used for local dev (see README), not
# a mocked/in-memory DB - we rely on Postgres-specific types (ARRAY, ENUM)
# that SQLite can't represent, so a real Postgres instance is the honest choice.
engine = create_engine(settings.database_url)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db_session():
    """Each test runs inside a transaction that's rolled back afterward,
    so tests never leave data behind or interfere with each other."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
