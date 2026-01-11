---
name: pytest-fastapi
description: Ensure FastAPI applications have comprehensive test coverage. Supports TDD (Test-Driven Development) workflow - write tests first, then implement. Analyzes routes, models, and schemas to identify missing tests, generates pytest test files with proper fixtures, runs tests with coverage. Use when doing TDD in FastAPI, asked to "write tests first", "test-driven development", "write tests", "check coverage", "generate tests for FastAPI", "run pytest", or "what needs testing".
---

# Pytest for FastAPI

Analyze, generate, and run tests for FastAPI applications. Supports TDD workflow.

## TDD Workflow (Test-Driven Development)

```
1. RED    → Write a failing test for the feature
2. GREEN  → Write minimal code to make the test pass
3. REFACTOR → Clean up code while keeping tests green
```

### TDD Example
```python
# Step 1: Write failing test first
def test_create_user(client):
    response = client.post("/users/", json={"email": "new@example.com", "name": "New User"})
    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"

# Step 2: Run test → FAILS (route doesn't exist yet)
# Step 3: Implement the route to make it pass
# Step 4: Run test → PASSES
# Step 5: Refactor if needed, ensure test still passes
```

## Coverage Workflow

### 1. Analyze Coverage
```bash
# Check what's tested
pytest --cov=app --cov-report=term-missing

# Generate HTML report
pytest --cov=app --cov-report=html
```

### 2. Identify Missing Tests

Scan the codebase for untested code:

| Look For | Test Needed |
|----------|-------------|
| `@app.get/post/put/delete` | Route handler test |
| `class *Model(Base)` | Model creation test |
| `class *Schema(BaseModel)` | Schema validation test |
| `def get_*` dependencies | Dependency injection test |
| Exception handlers | Error response test |

### 3. Generate Tests

For each untested component, create tests in `tests/` directory:

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_main.py         # Root endpoints
├── test_users.py        # User routes
└── test_models.py       # Model tests
```

## Essential Setup

### conftest.py (Required)
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from main import app

# In-memory SQLite for tests
SQLALCHEMY_TEST_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

### pyproject.toml or pytest.ini
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short"
```

## Test Patterns

### Route Tests
```python
def test_create_item(client):
    response = client.post("/items/", json={"name": "Test", "price": 10.5})
    assert response.status_code == 201
    assert response.json()["name"] == "Test"

def test_get_item_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

### Auth Tests
```python
def test_protected_route_unauthorized(client):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_protected_route_authorized(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
```

### Validation Tests
```python
def test_invalid_email(client):
    response = client.post("/users/", json={"email": "invalid", "name": "Test"})
    assert response.status_code == 422

def test_missing_required_field(client):
    response = client.post("/users/", json={"name": "Test"})  # missing email
    assert response.status_code == 422
```

## Commands

```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_users.py

# Run specific test
pytest tests/test_users.py::test_create_user

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run with coverage threshold (fail if below 80%)
pytest --cov=app --cov-fail-under=80
```

## Coverage Checklist

Before considering tests complete, verify:

- [ ] All routes have happy path tests
- [ ] All routes have error case tests (404, 422, 401)
- [ ] All Pydantic schemas have validation tests
- [ ] All database models can be created/queried
- [ ] Auth flows tested (login, protected routes)
- [ ] Edge cases covered (empty lists, duplicates)

## Resources

For detailed test patterns and examples, see [references/test-patterns.md](references/test-patterns.md).
