"""
Tests for Task CRUD API endpoints.

Test naming convention: test_<action>_<scenario>
Example: test_create_task_success, test_get_task_not_found
"""

from fastapi.testclient import TestClient


# =============================================================================
# CREATE (POST /tasks)
# =============================================================================

def test_create_task_success(client: TestClient):
    """Test creating a task with valid data."""
    response = client.post(
        "/tasks",
        json={"title": "Buy groceries", "description": "Milk and eggs"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy groceries"
    assert data["description"] == "Milk and eggs"
    assert data["completed"] is False  # Default value
    assert "id" in data  # ID should be auto-generated


def test_create_task_minimal(client: TestClient):
    """Test creating a task with only required fields."""
    response = client.post(
        "/tasks",
        json={"title": "Simple task"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Simple task"
    assert data["description"] is None  # Optional field
    assert data["completed"] is False


def test_create_task_missing_title(client: TestClient):
    """Test that title is required."""
    response = client.post(
        "/tasks",
        json={"description": "No title provided"},
    )

    assert response.status_code == 422  # Validation error


def test_create_task_empty_title(client: TestClient):
    """Test that empty title is rejected."""
    response = client.post(
        "/tasks",
        json={"title": ""},
    )

    assert response.status_code == 422  # Validation error (min_length=1)


# =============================================================================
# READ (GET /tasks, GET /tasks/{id})
# =============================================================================

def test_get_tasks_empty(client: TestClient):
    """Test getting tasks when none exist."""
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_get_tasks_with_data(client: TestClient):
    """Test getting all tasks."""
    # Create two tasks
    client.post("/tasks", json={"title": "Task 1"})
    client.post("/tasks", json={"title": "Task 2"})

    response = client.get("/tasks")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Task 1"
    assert data[1]["title"] == "Task 2"


def test_get_task_success(client: TestClient):
    """Test getting a single task by ID."""
    # Create a task first
    create_response = client.post(
        "/tasks",
        json={"title": "Test task", "description": "Test description"},
    )
    task_id = create_response.json()["id"]

    # Get the task
    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Test task"


def test_get_task_not_found(client: TestClient):
    """Test getting a non-existent task returns 404."""
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# =============================================================================
# UPDATE (PUT /tasks/{id})
# =============================================================================

def test_update_task_success(client: TestClient):
    """Test updating a task."""
    # Create a task
    create_response = client.post("/tasks", json={"title": "Original title"})
    task_id = create_response.json()["id"]

    # Update it
    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated title", "completed": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated title"
    assert data["completed"] is True


def test_update_task_partial(client: TestClient):
    """Test partial update (only some fields)."""
    # Create a task
    create_response = client.post(
        "/tasks",
        json={"title": "Original", "description": "Original desc"},
    )
    task_id = create_response.json()["id"]

    # Update only completed field
    response = client.put(
        f"/tasks/{task_id}",
        json={"completed": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Original"  # Unchanged
    assert data["description"] == "Original desc"  # Unchanged
    assert data["completed"] is True  # Updated


def test_update_task_not_found(client: TestClient):
    """Test updating a non-existent task returns 404."""
    response = client.put(
        "/tasks/999",
        json={"title": "New title"},
    )

    assert response.status_code == 404


# =============================================================================
# DELETE (DELETE /tasks/{id})
# =============================================================================

def test_delete_task_success(client: TestClient):
    """Test deleting a task."""
    # Create a task
    create_response = client.post("/tasks", json={"title": "To be deleted"})
    task_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 204
    assert response.content == b""  # Empty body

    # Verify it's gone
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404


def test_delete_task_not_found(client: TestClient):
    """Test deleting a non-existent task returns 404."""
    response = client.delete("/tasks/999")

    assert response.status_code == 404


# =============================================================================
# HEALTH CHECK
# =============================================================================

def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
