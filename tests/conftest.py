"""Shared pytest fixtures.

Uses an isolated temporary SQLite database so tests never touch a developer's
real gateway database. The DATABASE_URL is set before any application module is
imported so the engine binds to the temporary file.
"""
import os
import tempfile

import pytest

# Point the application at a throwaway database before importing app modules.
_TMP_DB = os.path.join(tempfile.gettempdir(), "test_sports_agent_gateway.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Recreate all tables before each test for isolation."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)
