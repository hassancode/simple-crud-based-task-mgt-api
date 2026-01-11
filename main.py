from collections.abc import Generator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session, SQLModel, Field, create_engine

# =============================================================================
# MODELS
# =============================================================================
# SQLModel uses Python type hints to define both database schema AND validation
#
# We create multiple model classes for different purposes:
# - TaskBase: Shared fields (used as a parent class)
# - Task: The actual database table (has id, used for DB operations)
# - TaskCreate: For creating new tasks (no id - database generates it)
# - TaskUpdate: For updating tasks (all fields optional)
# =============================================================================


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


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# SQLite stores the database in a local file called "tasks.db"
# For PostgreSQL, you'd use: "postgresql://user:password@localhost:5432/dbname"
# =============================================================================

DATABASE_URL = "sqlite:///tasks.db"

# Create the database engine
# - The engine is the starting point for any SQLAlchemy/SQLModel application
# - It manages the connection pool to the database
# - connect_args={"check_same_thread": False} is needed for SQLite only
#   (SQLite by default only allows one thread, but FastAPI is multi-threaded)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    """
    Create all database tables based on SQLModel classes with table=True.

    SQLModel.metadata.create_all() looks at all model classes and creates
    the corresponding tables if they don't exist.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session for each request.

    This is a generator function (uses yield instead of return):
    1. Creates a new Session when a request comes in
    2. Yields it to the endpoint function
    3. Automatically closes it after the request completes

    Using 'with' ensures the session is properly closed even if an error occurs.
    """
    with Session(engine) as session:
        yield session


# Type alias for cleaner endpoint signatures
# Instead of: session: Session = Depends(get_session)
# We can use: session: SessionDep
SessionDep = Depends(get_session)


# =============================================================================
# APP CONFIGURATION
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager - the modern way to handle startup/shutdown.

    This replaces the deprecated @app.on_event("startup") decorator.

    How it works:
    - Code BEFORE 'yield' runs on startup (before accepting requests)
    - Code AFTER 'yield' runs on shutdown (cleanup)

    In production, you'd typically use migrations (like Alembic) instead
    of create_db_and_tables().
    """
    # STARTUP
    create_db_and_tables()
    yield
    # SHUTDOWN (cleanup would go here if needed)


# Create the FastAPI application instance
# This is the main entry point for our API
app = FastAPI(
    title="Task Management API",
    description="A simple CRUD API for managing tasks",
    version="1.0.0",
    lifespan=lifespan  # Pass the lifespan context manager
)


# =============================================================================
# ENDPOINTS
# =============================================================================

# A simple health check endpoint
# The @app.get decorator tells FastAPI this function handles GET requests to "/"
@app.get("/")
def health_check():
    """Returns a simple message to confirm the API is running."""
    return {"status": "healthy", "message": "Task Management API is running"}


# -----------------------------------------------------------------------------
# CREATE - POST /tasks
# -----------------------------------------------------------------------------
@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: TaskCreate, session: Session = SessionDep):
    """
    Create a new task.

    How it works:
    1. FastAPI automatically parses the JSON request body into a TaskCreate object
    2. TaskCreate validates the data (title required, lengths checked, etc.)
    3. We convert TaskCreate → Task (the database model)
    4. session.add() stages the task for insertion
    5. session.commit() saves it to the database
    6. session.refresh() reloads the task to get the auto-generated id
    7. Return the task with its new id

    Parameters:
    - task: The task data from the request body (validated by TaskCreate)
    - session: Database session (injected by FastAPI via Depends)

    Returns:
    - The created task with its auto-generated id
    - HTTP 201 Created status code
    """
    # Convert the input schema to a database model
    # model_dump() converts the Pydantic model to a dict
    # **dict unpacks it as keyword arguments to Task()
    db_task = Task(**task.model_dump())

    # Add to session (staged for insert, not yet saved)
    session.add(db_task)

    # Commit the transaction (actually saves to database)
    session.commit()

    # Refresh to get the auto-generated id from the database
    session.refresh(db_task)

    return db_task
