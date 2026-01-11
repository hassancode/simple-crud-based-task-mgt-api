from fastapi import FastAPI
from sqlmodel import SQLModel, Field

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
# APP CONFIGURATION
# =============================================================================

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
