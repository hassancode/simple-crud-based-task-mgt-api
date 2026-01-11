---
name: fastapi-builder
description: Build FastAPI applications with proper project structure, routes, Pydantic models, SQLAlchemy database setup, and authentication. Use when creating new FastAPI projects, adding endpoints, setting up databases, or implementing auth. Triggers on "create FastAPI app", "build API with FastAPI", "FastAPI boilerplate", "add FastAPI endpoint", "FastAPI project".
---

# FastAPI Builder

Generate FastAPI projects with proper structure and common patterns for learning and development.

## Quick Start Templates

| Template | Use Case | Copy From |
|----------|----------|-----------|
| Hello World | Learning basics | `assets/hello-world/` |
| REST API + DB | CRUD operations | `assets/rest-api-db/` |

## Project Structure

```
my-api/
├── main.py                 # App entry point, uvicorn target
├── requirements.txt        # Dependencies
├── .env                    # Environment variables (DB_URL, SECRET_KEY)
└── app/
    ├── __init__.py
    ├── database.py         # SQLAlchemy engine & session
    ├── models/             # SQLAlchemy ORM models
    │   ├── __init__.py
    │   └── user.py
    ├── schemas/            # Pydantic request/response models
    │   ├── __init__.py
    │   └── user.py
    └── routers/            # API route handlers
        ├── __init__.py
        └── users.py
```

## Essential Code Patterns

### 1. Basic App (main.py)
```python
from fastapi import FastAPI
from app.routers import users

app = FastAPI(title="My API", version="1.0.0")

app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

### 2. Pydantic Schema
```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True
```

### 3. SQLAlchemy Model
```python
from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
```

### 4. Router with CRUD
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter()

@router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

### 5. Database Setup
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Commands

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install fastapi uvicorn sqlalchemy pydantic python-dotenv

# Run dev server
uvicorn main:app --reload

# Run on different port
uvicorn main:app --reload --port 8080
```

## Workflow

1. Copy template from `assets/` to project directory
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` with database URL
4. Run: `uvicorn main:app --reload`
5. Visit: http://localhost:8000/docs (Swagger UI)

## Resources

For advanced patterns (auth, middleware, testing), see [references/patterns.md](references/patterns.md).
