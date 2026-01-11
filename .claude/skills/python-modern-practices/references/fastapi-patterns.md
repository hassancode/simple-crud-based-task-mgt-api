# FastAPI Modern Patterns Reference

## Lifespan Context Manager (Full Example)

The lifespan context manager replaces the deprecated `@app.on_event()` decorators.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.

    Code before 'yield' runs on startup.
    Code after 'yield' runs on shutdown.
    """
    # STARTUP
    print("Starting up...")
    create_db_and_tables()
    # You can also:
    # - Initialize connection pools
    # - Load ML models
    # - Start background tasks

    yield  # Application runs here

    # SHUTDOWN
    print("Shutting down...")
    # Clean up resources:
    # - Close database connections
    # - Stop background tasks
    # - Release resources

app = FastAPI(
    title="My API",
    lifespan=lifespan  # Pass the lifespan function here
)
```

## Dependency Injection Patterns

### Using Annotated (Recommended)

```python
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session

def get_session():
    with Session(engine) as session:
        yield session

# Create a reusable type alias
SessionDep = Annotated[Session, Depends(get_session)]

# Use in endpoints - cleaner signature
@app.get("/items")
def get_items(session: SessionDep):
    return session.exec(select(Item)).all()
```

### Multiple Dependencies

```python
from typing import Annotated

CurrentUser = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]

@app.post("/items")
def create_item(
    item: ItemCreate,
    session: SessionDep,
    user: CurrentUser
):
    # Both dependencies are injected
    pass
```

## HTTP Exception Handling

```python
from fastapi import HTTPException, status

@app.get("/tasks/{task_id}")
def get_task(task_id: int, session: SessionDep):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )
    return task
```

## Response Models

```python
from fastapi import status

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, session: SessionDep) -> Task:
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task
```

## SQLModel Query Patterns

### Select with filtering

```python
from sqlmodel import select

# Get all
tasks = session.exec(select(Task)).all()

# Filter
completed = session.exec(
    select(Task).where(Task.completed == True)
).all()

# Get one or None
task = session.exec(
    select(Task).where(Task.id == task_id)
).first()

# Get by primary key (shortcut)
task = session.get(Task, task_id)
```

### Updating Records

```python
def update_task(task_id: int, task_update: TaskUpdate, session: SessionDep):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Only update provided fields
    task_data = task_update.model_dump(exclude_unset=True)
    db_task.sqlmodel_update(task_data)

    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task
```

### Deleting Records

```python
def delete_task(task_id: int, session: SessionDep):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()
    return {"ok": True}
```
