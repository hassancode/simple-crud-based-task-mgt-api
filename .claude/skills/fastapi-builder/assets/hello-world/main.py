"""
FastAPI Hello World
Run with: uvicorn main:app --reload
"""
from fastapi import FastAPI

app = FastAPI(
    title="Hello World API",
    description="A simple FastAPI application",
    version="1.0.0"
)


@app.get("/")
def read_root():
    """Root endpoint returning a welcome message."""
    return {"message": "Hello, World!"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    """
    Get an item by ID with optional query parameter.

    - **item_id**: The ID of the item (path parameter)
    - **q**: Optional query string
    """
    return {"item_id": item_id, "query": q}


@app.post("/items")
def create_item(name: str, price: float):
    """Create a new item."""
    return {"name": name, "price": price, "message": "Item created"}
