"""
Tests for main application endpoints.
"""


def test_root_endpoint(client):
    """Test the root endpoint returns welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# Add more tests for your routes below:

# def test_create_item(client):
#     """Test creating a new item."""
#     response = client.post(
#         "/items/",
#         json={"name": "Test Item", "price": 10.99}
#     )
#     assert response.status_code == 201
#     data = response.json()
#     assert data["name"] == "Test Item"
#     assert "id" in data
