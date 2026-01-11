# FastAPI Test Patterns

## Table of Contents
- [CRUD Route Tests](#crud-route-tests)
- [Authentication Tests](#authentication-tests)
- [Validation Tests](#validation-tests)
- [Database Tests](#database-tests)
- [Async Tests](#async-tests)
- [Fixtures](#fixtures)
- [Mocking](#mocking)

---

## CRUD Route Tests

### Create (POST)
```python
def test_create_user_success(client):
    """Test successful user creation."""
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "name": "Test User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data

def test_create_user_duplicate_email(client, db):
    """Test duplicate email returns 400."""
    # Create first user
    client.post("/users/", json={"email": "test@example.com", "name": "First"})
    # Try to create duplicate
    response = client.post("/users/", json={"email": "test@example.com", "name": "Second"})
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()
```

### Read (GET)
```python
def test_get_user_success(client):
    """Test getting existing user."""
    # Create user first
    create_response = client.post("/users/", json={"email": "test@example.com", "name": "Test"})
    user_id = create_response.json()["id"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_get_user_not_found(client):
    """Test 404 for non-existent user."""
    response = client.get("/users/99999")
    assert response.status_code == 404

def test_get_users_list(client):
    """Test listing users with pagination."""
    # Create multiple users
    for i in range(5):
        client.post("/users/", json={"email": f"user{i}@example.com", "name": f"User {i}"})

    response = client.get("/users/?skip=0&limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_get_users_empty(client):
    """Test empty list when no users."""
    response = client.get("/users/")
    assert response.status_code == 200
    assert response.json() == []
```

### Update (PUT/PATCH)
```python
def test_update_user_success(client):
    """Test updating user."""
    create_response = client.post("/users/", json={"email": "old@example.com", "name": "Old Name"})
    user_id = create_response.json()["id"]

    response = client.put(f"/users/{user_id}", json={"name": "New Name"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"

def test_update_user_not_found(client):
    """Test updating non-existent user."""
    response = client.put("/users/99999", json={"name": "New Name"})
    assert response.status_code == 404
```

### Delete (DELETE)
```python
def test_delete_user_success(client):
    """Test deleting user."""
    create_response = client.post("/users/", json={"email": "test@example.com", "name": "Test"})
    user_id = create_response.json()["id"]

    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 404

def test_delete_user_not_found(client):
    """Test deleting non-existent user."""
    response = client.delete("/users/99999")
    assert response.status_code == 404
```

---

## Authentication Tests

### Login Tests
```python
def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401

def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "pass"}
    )
    assert response.status_code == 401
```

### Protected Route Tests
```python
def test_protected_route_no_token(client):
    """Test accessing protected route without token."""
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_protected_route_invalid_token(client):
    """Test accessing protected route with invalid token."""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_protected_route_expired_token(client, expired_token):
    """Test accessing protected route with expired token."""
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

def test_protected_route_valid_token(client, auth_headers):
    """Test accessing protected route with valid token."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
```

---

## Validation Tests

### Pydantic Schema Validation
```python
def test_invalid_email_format(client):
    """Test validation rejects invalid email."""
    response = client.post("/users/", json={"email": "not-an-email", "name": "Test"})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("email" in str(e).lower() for e in errors)

def test_missing_required_field(client):
    """Test validation requires email field."""
    response = client.post("/users/", json={"name": "Test"})
    assert response.status_code == 422

def test_empty_string_validation(client):
    """Test validation rejects empty strings if required."""
    response = client.post("/users/", json={"email": "test@example.com", "name": ""})
    assert response.status_code == 422

def test_wrong_type(client):
    """Test validation rejects wrong types."""
    response = client.post("/items/", json={"name": "Test", "price": "not-a-number"})
    assert response.status_code == 422

def test_negative_value_validation(client):
    """Test validation rejects negative price."""
    response = client.post("/items/", json={"name": "Test", "price": -10})
    assert response.status_code == 422
```

---

## Database Tests

### Model Tests
```python
def test_user_model_creation(db):
    """Test creating user model directly."""
    from app.models import User

    user = User(email="test@example.com", name="Test User")
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.created_at is not None

def test_user_model_unique_email(db):
    """Test unique email constraint."""
    from app.models import User
    from sqlalchemy.exc import IntegrityError
    import pytest

    user1 = User(email="test@example.com", name="User 1")
    db.add(user1)
    db.commit()

    user2 = User(email="test@example.com", name="User 2")
    db.add(user2)
    with pytest.raises(IntegrityError):
        db.commit()
```

---

## Async Tests

### Async Route Tests
```python
import pytest

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    """Test async endpoint."""
    response = await async_client.get("/async-data")
    assert response.status_code == 200

# conftest.py for async
@pytest.fixture
async def async_client():
    from httpx import AsyncClient
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

---

## Fixtures

### Common Fixtures
```python
# conftest.py

@pytest.fixture
def test_user(client, db):
    """Create a test user and return it."""
    from app.core.security import hash_password
    from app.models import User

    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=hash_password("testpass123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(client, test_user):
    """Get auth headers for test user."""
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_items(client, auth_headers):
    """Create sample items for testing."""
    items = []
    for i in range(3):
        response = client.post(
            "/items/",
            json={"name": f"Item {i}", "price": 10.0 * (i + 1)},
            headers=auth_headers
        )
        items.append(response.json())
    return items
```

---

## Mocking

### Mock External Services
```python
from unittest.mock import patch, MagicMock

def test_send_email_on_registration(client):
    """Test email is sent when user registers."""
    with patch("app.services.email.send_email") as mock_send:
        mock_send.return_value = True

        response = client.post("/users/", json={"email": "test@example.com", "name": "Test"})

        assert response.status_code == 201
        mock_send.assert_called_once_with("test@example.com", subject="Welcome!")

def test_external_api_failure(client):
    """Test handling external API failure."""
    with patch("app.services.external.fetch_data") as mock_fetch:
        mock_fetch.side_effect = Exception("API unavailable")

        response = client.get("/external-data")

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()
```

### Mock Database
```python
def test_with_mocked_db_query(client):
    """Test with mocked database query."""
    with patch("app.routers.users.get_user_by_id") as mock_get:
        mock_get.return_value = {"id": 1, "email": "mock@example.com", "name": "Mock"}

        response = client.get("/users/1")

        assert response.status_code == 200
        assert response.json()["email"] == "mock@example.com"
```

---

## Test Requirements

```txt
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
```
