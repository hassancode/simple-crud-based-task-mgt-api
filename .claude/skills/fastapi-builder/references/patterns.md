# FastAPI Advanced Patterns

## Table of Contents
- [Authentication](#authentication)
- [Middleware](#middleware)
- [Error Handling](#error-handling)
- [Background Tasks](#background-tasks)
- [Testing](#testing)
- [Async Patterns](#async-patterns)

---

## Authentication

### JWT Token Auth
```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

### Auth Dependency
```python
# app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from app.core.security import decode_token
from app.database import get_db
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
```

### Protected Route
```python
from fastapi import Depends
from app.core.deps import get_current_user

@router.get("/me")
def get_current_user_info(current_user = Depends(get_current_user)):
    return current_user
```

---

## Middleware

### CORS
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Request Logging
```python
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"{request.method} {request.url.path} - {process_time:.3f}s")
    return response
```

---

## Error Handling

### Custom Exception Handler
```python
from fastapi import Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

# Usage
raise AppException(status_code=400, detail="Invalid input")
```

### Validation Error Handler
```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"]
        })
    return JSONResponse(
        status_code=422,
        content={"errors": errors}
    )
```

---

## Background Tasks

### Simple Background Task
```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Simulate email sending
    print(f"Sending email to {email}: {message}")

@router.post("/register")
def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    # Create user...
    background_tasks.add_task(send_email, user.email, "Welcome!")
    return {"message": "User created"}
```

---

## Testing

### Test Setup (conftest.py)
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from main import app

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Test Example
```python
def test_create_user(client):
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_get_user(client):
    # Create user first
    client.post("/users/", json={"email": "test@example.com", "name": "Test"})

    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_user_not_found(client):
    response = client.get("/users/999")
    assert response.status_code == 404
```

---

## Async Patterns

### Async Route with httpx
```python
import httpx
from fastapi import APIRouter

router = APIRouter()

@router.get("/external-data")
async def get_external_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### Async Database (with async SQLAlchemy)
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_db():
    async with async_session() as session:
        yield session

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

---

## Requirements for Advanced Features

```txt
# Auth
python-jose[cryptography]
passlib[bcrypt]

# Async HTTP
httpx

# Async DB
asyncpg
sqlalchemy[asyncio]

# Testing
pytest
pytest-asyncio
```
