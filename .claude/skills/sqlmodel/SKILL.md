---
name: sqlmodel
description: Database design and management using SQLModel (SQLAlchemy + Pydantic combined). Create models, relationships, CRUD operations, and integrate with FastAPI. Use when designing database schemas, creating SQLModel models, adding relationships (one-to-many, many-to-many), performing migrations, or building database-backed APIs. Triggers on "SQLModel", "database model", "database design", "add relationship", "create table".
---

# SQLModel

Database design and management combining SQLAlchemy power with Pydantic validation.

## Why SQLModel over SQLAlchemy?

| Feature | SQLModel | SQLAlchemy |
|---------|----------|------------|
| Single class for DB + API | Yes | No (need separate Pydantic) |
| Type hints | Built-in | Manual |
| FastAPI integration | Native | Requires adapters |
| Pydantic validation | Built-in | Separate schemas |

## Setup

```bash
pip install sqlmodel
```

```python
from sqlmodel import SQLModel, Field, create_engine, Session

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

## Basic Model

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## Model Patterns

### Read vs Create/Update Schemas
```python
# Base with shared fields
class UserBase(SQLModel):
    email: str
    name: str

# For creating (no id)
class UserCreate(UserBase):
    password: str

# For reading (has id)
class UserRead(UserBase):
    id: int

# Database table
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
```

### Field Options
```python
class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)                    # Indexed
    price: float = Field(ge=0)                       # Validation: >= 0
    code: str = Field(unique=True)                   # Unique constraint
    description: Optional[str] = Field(default=None) # Nullable
    quantity: int = Field(default=0)                 # Default value
```

## CRUD Operations

```python
from sqlmodel import Session, select

# Create
def create_user(session: Session, user: UserCreate) -> User:
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# Read
def get_user(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)

def get_users(session: Session, skip: int = 0, limit: int = 100) -> list[User]:
    statement = select(User).offset(skip).limit(limit)
    return session.exec(statement).all()

# Update
def update_user(session: Session, user_id: int, user_update: UserUpdate) -> User:
    db_user = session.get(User, user_id)
    user_data = user_update.model_dump(exclude_unset=True)
    for key, value in user_data.items():
        setattr(db_user, key, value)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# Delete
def delete_user(session: Session, user_id: int) -> bool:
    user = session.get(User, user_id)
    if user:
        session.delete(user)
        session.commit()
        return True
    return False
```

## FastAPI Integration

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Resources

- **Relationships**: See [references/relationships.md](references/relationships.md) for one-to-many, many-to-many patterns
- **Templates**: Copy from `assets/` for project boilerplate
