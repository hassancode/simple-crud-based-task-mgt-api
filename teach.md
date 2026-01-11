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

### What is SQLite?

SQLite is a lightweight, file-based database:
- **Zero installation** - Built into Python
- **File-based** - Stores everything in a single `.db` file
- **Same ORM code** - SQLModel code works identically with PostgreSQL
- **Perfect for development** - Easy to switch to PostgreSQL for production

### Key Concepts

1. **Engine** - The connection to the database (like opening a file handle)
2. **Session** - A "conversation" with the database where you run queries
3. **Dependency Injection** - FastAPI's pattern for providing resources to endpoints

### The Code

```python
from collections.abc import Generator
from fastapi import Depends
from sqlmodel import Session, create_engine

# SQLite connection string - creates a file called "tasks.db"
# For PostgreSQL: "postgresql://user:password@localhost:5432/dbname"
DATABASE_URL = "sqlite:///tasks.db"

# Create the database engine
# connect_args is needed for SQLite only (thread safety)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """Create all tables based on SQLModel classes with table=True."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session for each request.

    Generator function (uses yield):
    1. Creates a new Session when a request comes in
    2. Yields it to the endpoint function
    3. Automatically closes it after the request completes
    """
    with Session(engine) as session:
        yield session


# Type alias for cleaner endpoint signatures
SessionDep = Depends(get_session)
```

### Lifespan Context Manager (Modern Pattern)

The old `@app.on_event("startup")` decorator is **deprecated**. Use the lifespan context manager instead:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown.

    - Code BEFORE yield = startup (runs before accepting requests)
    - Code AFTER yield = shutdown (cleanup)
    """
    # STARTUP
    create_db_and_tables()
    yield
    # SHUTDOWN (cleanup here if needed)

app = FastAPI(
    title="My API",
    lifespan=lifespan  # Pass the lifespan function
)
```

**Why lifespan is better:**
- Single place for both startup AND shutdown logic
- Cleaner resource management (like context managers)
- Follows modern Python async patterns
- The deprecated `on_event` will be removed in future FastAPI versions

### Understanding Dependency Injection

FastAPI's `Depends()` is powerful. When you write:

```python
@app.get("/tasks")
def get_tasks(session: Session = Depends(get_session)):
    # session is automatically provided!
```

FastAPI will:
1. Call `get_session()` before your function runs
2. Pass the yielded `Session` to your function
3. Continue the generator (cleanup) after your function returns

This ensures:
- Each request gets its own database session
- Sessions are properly closed even if errors occur
- You don't have to manually manage connections

### SQLite vs PostgreSQL

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Installation | None (built-in) | Requires server |
| Storage | Single file | Client-server |
| Concurrency | Limited | Excellent |
| Use case | Development, small apps | Production |
| Connection string | `sqlite:///file.db` | `postgresql://user:pass@host/db` |

To switch to PostgreSQL later, just change `DATABASE_URL` and remove `connect_args`!

---

## Step 4: Create POST Endpoint (Create Task)

### What is CRUD?

CRUD represents the four basic operations for persistent storage:

| Operation | HTTP Method | SQL Equivalent | Description |
|-----------|-------------|----------------|-------------|
| **C**reate | POST | INSERT | Add new data |
| **R**ead | GET | SELECT | Retrieve data |
| **U**pdate | PUT/PATCH | UPDATE | Modify data |
| **D**elete | DELETE | DELETE | Remove data |

### Common HTTP Status Codes

| Code | Name | When to Use |
|------|------|-------------|
| 200 | OK | Success (default) |
| 201 | Created | Successfully created a new resource |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |

### The Code

```python
@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate, session: Session = SessionDep):
    """Create a new task."""
    # Convert input schema to database model
    db_task = Task(**task.model_dump())

    # Add to session (staged for insert)
    session.add(db_task)

    # Commit (save to database)
    session.commit()

    # Refresh to get auto-generated id
    session.refresh(db_task)

    return db_task
```

### Understanding the Decorator

```python
@app.post("/tasks", response_model=Task, status_code=201)
```

- `@app.post("/tasks")` - Handle POST requests to `/tasks`
- `response_model=Task` - Serialize the response using the Task model
- `status_code=201` - Return 201 Created instead of default 200 OK

### Understanding the Function Parameters

```python
def create_task(task: TaskCreate, session: Session = SessionDep):
```

- `task: TaskCreate` - FastAPI automatically:
  1. Reads the JSON request body
  2. Validates it against TaskCreate schema
  3. Returns 422 error if validation fails
  4. Passes the validated object to your function

- `session: Session = SessionDep` - Dependency injection provides the database session

### The Database Operations Flow

```
Client Request          FastAPI                    Database
     |                    |                           |
     |--- POST /tasks --->|                           |
     |    {title: "..."}  |                           |
     |                    |-- validate (TaskCreate) --|
     |                    |                           |
     |                    |-- Task(**data) ---------->|
     |                    |-- session.add() --------->|
     |                    |-- session.commit() ------>| INSERT INTO tasks...
     |                    |<- session.refresh() ------|
     |                    |   (gets new id)           |
     |<-- 201 + Task -----|                           |
```

### Key Methods Explained

| Method | What it Does |
|--------|--------------|
| `task.model_dump()` | Converts Pydantic model to dictionary |
| `Task(**dict)` | Creates Task instance from dict (unpacking) |
| `session.add(obj)` | Stages object for insertion (not saved yet) |
| `session.commit()` | Saves all staged changes to database |
| `session.refresh(obj)` | Reloads object from DB (gets generated values) |

### Testing with curl

```bash
# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "description": "Milk, eggs, bread"}'

# Response:
# {"title": "Buy groceries", "description": "Milk, eggs, bread", "completed": false, "id": 1}
```

Or use the interactive docs at `http://localhost:8000/docs`!

---

## Step 5: Create GET Endpoints (Read Tasks)

We create two GET endpoints for reading data:
1. **GET /tasks** - List all tasks
2. **GET /tasks/{task_id}** - Get a single task by ID

### GET All Tasks

```python
@app.get("/tasks", response_model=list[Task])
def get_tasks(session: Session = SessionDep):
    """Get all tasks."""
    statement = select(Task)
    tasks = session.exec(statement).all()
    return tasks
```

**Key points:**
- `response_model=list[Task]` - Returns a JSON array of tasks
- `select(Task)` - Creates a SELECT query (SQL: `SELECT * FROM task`)
- `session.exec().all()` - Executes query and returns all results as a list

### GET Single Task by ID

```python
@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, session: Session = SessionDep):
    """Get a single task by ID."""
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found"
        )

    return task
```

### Path Parameters

The `{task_id}` in the URL path becomes a function parameter:

```
URL: /tasks/5
         ↓
def get_task(task_id: int, ...):
             ↑
        task_id = 5
```

FastAPI automatically:
- Extracts the value from the URL
- Validates it matches the type hint (`int`)
- Returns 422 error if validation fails (e.g., `/tasks/abc`)

### HTTPException

When something goes wrong, raise `HTTPException`:

```python
from fastapi import HTTPException

raise HTTPException(
    status_code=404,              # HTTP status code
    detail="Task not found"       # Error message in response body
)
```

**Response:**
```json
{
    "detail": "Task not found"
}
```

### Query Methods Comparison

| Method | Use Case | SQL Equivalent |
|--------|----------|----------------|
| `session.get(Model, id)` | Get by primary key | `SELECT * FROM task WHERE id = ?` |
| `session.exec(select(Model)).all()` | Get all records | `SELECT * FROM task` |
| `session.exec(select(Model)).first()` | Get first match | `SELECT * FROM task LIMIT 1` |

### Testing with curl

```bash
# Get all tasks
curl http://localhost:8000/tasks
# Response: [{"title": "Buy groceries", "description": "...", "completed": false, "id": 1}]

# Get single task
curl http://localhost:8000/tasks/1
# Response: {"title": "Buy groceries", "description": "...", "completed": false, "id": 1}

# Get non-existent task (404 error)
curl http://localhost:8000/tasks/999
# Response: {"detail": "Task with id 999 not found"}
```

---

## Step 6: Create PUT Endpoint (Update Task)

### PUT vs PATCH

| Method | Behavior | Use Case |
|--------|----------|----------|
| PUT | Replace entire resource | Send all fields, missing = null |
| PATCH | Partial update | Send only changed fields |

We implement PATCH-style behavior (more practical) using the PUT method.

### The Code

```python
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate, session: Session = SessionDep):
    """Update an existing task (partial update)."""
    # Fetch existing task
    db_task = session.get(Task, task_id)

    if not db_task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")

    # Get only fields that were explicitly provided
    update_data = task_update.model_dump(exclude_unset=True)

    # Update the task
    db_task.sqlmodel_update(update_data)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    return db_task
```

### The Magic of exclude_unset=True

This is the key to partial updates:

```python
# Request body: {"completed": true}
# (title and description NOT provided)

# WITHOUT exclude_unset=True:
task_update.model_dump()
# → {"title": None, "description": None, "completed": True}
# ❌ Would overwrite title and description with None!

# WITH exclude_unset=True:
task_update.model_dump(exclude_unset=True)
# → {"completed": True}
# ✅ Only updates what was provided
```

### sqlmodel_update()

SQLModel provides a convenient method to update multiple fields at once:

```python
# Instead of:
db_task.title = update_data.get("title", db_task.title)
db_task.completed = update_data.get("completed", db_task.completed)
# ...for each field

# Use:
db_task.sqlmodel_update(update_data)  # Updates all provided fields
```

### The Update Flow

```
Client                          Server                         Database
  |                               |                               |
  |-- PUT /tasks/1 -------------->|                               |
  |   {"completed": true}         |                               |
  |                               |-- session.get(Task, 1) ------>|
  |                               |<-- Task(id=1, ...) -----------|
  |                               |                               |
  |                               |-- model_dump(exclude_unset) --|
  |                               |   → {"completed": true}       |
  |                               |                               |
  |                               |-- sqlmodel_update() ----------|
  |                               |-- session.commit() ---------->| UPDATE task SET...
  |                               |                               |
  |<-- 200 + Updated Task --------|                               |
```

### Testing with curl

```bash
# Mark task as completed
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Update title only
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy organic groceries"}'

# Update multiple fields
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "New title", "description": "New desc", "completed": true}'
```

---

## Step 7: Create DELETE Endpoint (Delete Task)

The simplest CRUD operation - fetch, verify, delete.

### The Code

```python
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = SessionDep):
    """Delete a task by ID."""
    task = session.get(Task, task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")

    session.delete(task)
    session.commit()

    return None  # 204 No Content
```

### Why 204 No Content?

| Status Code | Meaning | Response Body |
|-------------|---------|---------------|
| 200 OK | Success, here's the data | Has content |
| 201 Created | Success, created resource | Has content (the created item) |
| 204 No Content | Success, nothing to return | Empty |

For DELETE:
- The resource no longer exists
- There's nothing meaningful to return
- 204 is the HTTP standard for "success, but no body"

### session.delete() vs session.add()

| Method | SQL | Purpose |
|--------|-----|---------|
| `session.add(obj)` | INSERT/UPDATE | Add or update a record |
| `session.delete(obj)` | DELETE | Remove a record |

Both require `session.commit()` to persist changes.

### Testing with curl

```bash
# Delete a task
curl -X DELETE http://localhost:8000/tasks/1 -v
# Response: HTTP 204 (empty body)

# Try to delete again (already deleted)
curl -X DELETE http://localhost:8000/tasks/1
# Response: {"detail": "Task with id 1 not found"}

# Verify it's gone
curl http://localhost:8000/tasks/1
# Response: {"detail": "Task with id 1 not found"}
```

### CRUD Complete!

You now have a fully functional REST API:

| Operation | Method | Endpoint | Status Code |
|-----------|--------|----------|-------------|
| Create | POST | /tasks | 201 Created |
| Read All | GET | /tasks | 200 OK |
| Read One | GET | /tasks/{id} | 200 OK |
| Update | PUT | /tasks/{id} | 200 OK |
| Delete | DELETE | /tasks/{id} | 204 No Content |

---

## Step 8: Add Tests with pytest

*Coming next...*
