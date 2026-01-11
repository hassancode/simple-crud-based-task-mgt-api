# Building a CRUD Task Management API - Step by Step Guide

This document compiles all the teaching and explanations from building this FastAPI + SQLModel project.

---

## Step 1: Basic FastAPI App

### What is FastAPI?

FastAPI is a modern Python web framework for building APIs. It's:
- **Fast** - One of the fastest Python frameworks
- **Type-safe** - Uses Python type hints for validation
- **Auto-documented** - Generates Swagger/OpenAPI docs automatically

### The Code

```python
from fastapi import FastAPI

# Create the FastAPI application instance
# This is the main entry point for our API
app = FastAPI(
    title="Task Management API",
    description="A simple CRUD API for managing tasks",
    version="1.0.0"
)


# A simple health check endpoint
# The @app.get decorator tells FastAPI this function handles GET requests to "/"
@app.get("/")
def health_check():
    """Returns a simple message to confirm the API is running."""
    return {"status": "healthy", "message": "Task Management API is running"}
```

### Explanation

1. **`from fastapi import FastAPI`** - Import the FastAPI class
2. **`app = FastAPI(...)`** - Create an app instance with metadata (title, description, version)
3. **`@app.get("/")`** - A decorator that registers a function to handle GET requests at the root path
4. **`health_check()`** - Returns a JSON response automatically (FastAPI converts dicts to JSON)

### How to Test

Run the server:
```bash
uv run uvicorn main:app --reload
```

Then visit:
- `http://localhost:8000` - See the health check response
- `http://localhost:8000/docs` - Auto-generated Swagger UI documentation

---

## Step 2: Define the Task Model with SQLModel

### What is SQLModel?

SQLModel combines two powerful libraries:
- **SQLAlchemy** - The most popular Python ORM (Object-Relational Mapper) for databases
- **Pydantic** - Data validation library (also used by FastAPI)

This means one model class can:
1. Define your database table schema
2. Validate incoming API data
3. Serialize data for API responses

### What is an ORM?

Instead of writing raw SQL like:
```sql
INSERT INTO tasks (title, completed) VALUES ('Buy milk', false)
```

You work with Python objects:
```python
Task(title="Buy milk", completed=False)
```

### The Code

```python
from sqlmodel import SQLModel, Field


class TaskBase(SQLModel):
    """Base model with shared fields. Not a database table."""
    title: str = Field(min_length=1, max_length=200)  # Required, 1-200 chars
    description: str | None = Field(default=None, max_length=1000)  # Optional
    completed: bool = Field(default=False)  # Defaults to False


class Task(TaskBase, table=True):
    """
    The actual database table model.

    - table=True tells SQLModel this creates a database table
    - id is optional in Python (None before saving) but required in DB
    - primary_key=True makes it auto-increment
    """
    id: int | None = Field(default=None, primary_key=True)


class TaskCreate(TaskBase):
    """
    Schema for creating a new task.

    Inherits title, description, completed from TaskBase.
    No id field - the database will generate it.
    """
    pass


class TaskUpdate(SQLModel):
    """
    Schema for updating a task.

    All fields are optional - only update what's provided.
    This allows PATCH-style partial updates.
    """
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None
```

### Model Comparison Table

| Model | Purpose | Has `id`? | `table=True`? |
|-------|---------|-----------|---------------|
| `TaskBase` | Shared fields (parent class) | No | No |
| `Task` | Database table + API responses | Yes (auto-generated) | Yes |
| `TaskCreate` | Validate POST request body | No | No |
| `TaskUpdate` | Validate PUT/PATCH request body | No | No |

### Key Concepts

1. **`Field(...)`** - Adds validation rules (min/max length, default values)
2. **`str | None`** - Python 3.10+ union syntax meaning "string or None" (optional)
3. **`table=True`** - Tells SQLModel to create a database table for this model
4. **`primary_key=True`** - Makes `id` auto-increment and unique

### Why Multiple Models?

- When **creating** a task, the client shouldn't send an `id` (DB generates it)
- When **updating**, all fields should be optional (partial updates)
- When **reading**, we return the full `Task` with `id`

---

## Step 3: Set up SQLite Database Connection

*Coming next...*

---

## Step 4: Create POST Endpoint (Create Task)

*Coming next...*

---

## Step 5: Create GET Endpoints (Read Tasks)

*Coming next...*

---

## Step 6: Create PUT Endpoint (Update Task)

*Coming next...*

---

## Step 7: Create DELETE Endpoint (Delete Task)

*Coming next...*

---

## Step 8: Add Tests with pytest

*Coming next...*
