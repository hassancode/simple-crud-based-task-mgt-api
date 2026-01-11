"""
Test configuration and fixtures.

This file is automatically discovered by pytest and provides fixtures
that can be used across all test files.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app, get_session


@pytest.fixture(name="session")
def session_fixture():
    """
    Create a fresh in-memory database for each test.

    Why in-memory SQLite?
    - Fast: No disk I/O
    - Isolated: Each test gets a fresh database
    - Clean: Database disappears after test

    StaticPool ensures the same connection is reused,
    which is required for in-memory SQLite.
    """
    # Create in-memory SQLite engine
    engine = create_engine(
        "sqlite://",  # Empty = in-memory database
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Required for in-memory SQLite
    )

    # Create all tables
    SQLModel.metadata.create_all(engine)

    # Create and yield session
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """
    Create a test client with overridden database session.

    How dependency override works:
    1. We tell FastAPI: "When get_session is called, use our test session instead"
    2. All endpoints now use the test database
    3. After the test, we clear the override

    This ensures tests don't affect the real database.
    """

    # Override the get_session dependency
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    # Create test client
    client = TestClient(app)

    yield client

    # Clean up: remove the override
    app.dependency_overrides.clear()
