"""
Pytest configuration and fixtures for FastAPI testing.
Copy this file to your project's tests/ directory.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from main import app


# Use in-memory SQLite for fast, isolated tests
SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Required for in-memory SQLite with multiple threads
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Create a fresh database for each test.
    Tables are created before and dropped after each test.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Create a test client with database dependency override.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Uncomment and customize these fixtures as needed:

# @pytest.fixture
# def test_user(db):
#     """Create a test user."""
#     from app.models import User
#     from app.core.security import hash_password
#
#     user = User(
#         email="test@example.com",
#         name="Test User",
#         hashed_password=hash_password("testpass123")
#     )
#     db.add(user)
#     db.commit()
#     db.refresh(user)
#     return user


# @pytest.fixture
# def auth_headers(client, test_user):
#     """Get authorization headers for authenticated requests."""
#     response = client.post(
#         "/auth/login",
#         data={"username": "test@example.com", "password": "testpass123"}
#     )
#     token = response.json()["access_token"]
#     return {"Authorization": f"Bearer {token}"}
