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
