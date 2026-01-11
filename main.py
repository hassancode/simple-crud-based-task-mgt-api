from collections.abc import Generator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, SQLModel, Field, create_engine, select

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


# -----------------------------------------------------------------------------
# READ - GET /tasks (list all)
# -----------------------------------------------------------------------------
@app.get("/tasks", response_model=list[Task])
def get_tasks(session: Session = SessionDep):
    """
    Get all tasks.

    How it works:
    1. select(Task) creates a SELECT query for the Task table
    2. session.exec() executes the query
    3. .all() fetches all results as a list

    The SQL equivalent: SELECT * FROM task

    Returns:
    - List of all tasks (empty list if none exist)
    """
    # Create a SELECT statement for all Tasks
    statement = select(Task)

    # Execute and get all results
    tasks = session.exec(statement).all()

    return tasks


# -----------------------------------------------------------------------------
# READ - GET /tasks/{task_id} (single task)
# -----------------------------------------------------------------------------
@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, session: Session = SessionDep):
    """
    Get a single task by ID.

    How it works:
    1. task_id comes from the URL path (e.g., /tasks/5 → task_id=5)
    2. session.get() is a shortcut to fetch by primary key
    3. If not found, we raise HTTPException with 404 status

    Parameters:
    - task_id: The task ID from the URL path (automatically validated as int)

    Returns:
    - The task if found
    - HTTP 404 Not Found if task doesn't exist
    """
    # session.get() fetches by primary key - cleaner than select().where()
    task = session.get(Task, task_id)

    # If no task found, return 404 error
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found"
        )

    return task


# -----------------------------------------------------------------------------
# UPDATE - PUT /tasks/{task_id}
# -----------------------------------------------------------------------------
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate, session: Session = SessionDep):
    """
    Update an existing task (partial update supported).

    How it works:
    1. Fetch the existing task from database
    2. If not found, return 404
    3. Get only the fields that were provided in the request (exclude_unset=True)
    4. Update only those fields on the existing task
    5. Save and return the updated task

    Why exclude_unset=True?
    - If user sends {"completed": true}, we only update 'completed'
    - Without it, title and description would be set to None

    Parameters:
    - task_id: The task ID from the URL path
    - task_update: The update data (all fields optional)

    Returns:
    - The updated task
    - HTTP 404 if task doesn't exist
    """
    # Fetch existing task
    db_task = session.get(Task, task_id)

    if not db_task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found"
        )

    # Get only the fields that were explicitly set in the request
    # exclude_unset=True ignores fields that weren't provided
    update_data = task_update.model_dump(exclude_unset=True)

    # Update each provided field on the database object
    # sqlmodel_update is a convenient method to update multiple fields
    db_task.sqlmodel_update(update_data)

    # Save changes
    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    return db_task
