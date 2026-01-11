"""
FastAPI REST API with Database
Run with: uvicorn main:app --reload
"""
from fastapi import FastAPI
from app.database import engine, Base
from app.routers import users

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="REST API with Database",
    description="FastAPI application with SQLAlchemy and Pydantic",
    version="1.0.0"
)

# Include routers
app.include_router(users.router, prefix="/users", tags=["users"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
