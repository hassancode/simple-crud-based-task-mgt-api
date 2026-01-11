---
name: python-modern-practices
description: Ensure Python code follows modern patterns and latest library APIs. Use when writing Python code, especially with FastAPI, SQLModel, Pydantic, or SQLAlchemy. Triggers on Python file creation/editing, API development, database models, or when user asks for "modern", "latest", or "best practices" Python code. Prevents deprecated patterns and uses current documentation.
---

# Python Modern Practices

Ensure all Python code uses modern patterns and the latest stable APIs. Before writing code, verify patterns against current documentation.

## Core Principles

1. **Verify before using** - Check if a pattern/API is current before writing code
2. **Prefer modern syntax** - Use Python 3.10+ features (union types `X | None`, match statements)
3. **Avoid deprecated APIs** - Never use deprecated functions even if they still work

## FastAPI Modern Patterns

### Lifespan (NOT on_event)

**DEPRECATED - Never use:**
```python
@app.on_event("startup")  # DEPRECATED!
def startup():
    pass
```

**MODERN - Always use:**
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs before app starts accepting requests
    create_db_and_tables()
    yield
    # Shutdown: runs when app is shutting down (cleanup here)

app = FastAPI(lifespan=lifespan)
```

### Type Annotations

**DEPRECATED:**
```python
from typing import Optional, List, Union
def func(x: Optional[str], items: List[int]) -> Union[str, None]:
```

**MODERN (Python 3.10+):**
```python
def func(x: str | None, items: list[int]) -> str | None:
```

### Pydantic V2

**DEPRECATED (Pydantic V1):**
```python
class Model(BaseModel):
    class Config:
        orm_mode = True

data = model.dict()
```

**MODERN (Pydantic V2):**
```python
class Model(BaseModel):
    model_config = ConfigDict(from_attributes=True)

data = model.model_dump()
```

### Annotated Dependencies

**OLD style:**
```python
def endpoint(session: Session = Depends(get_session)):
```

**MODERN style (optional but cleaner):**
```python
from typing import Annotated
SessionDep = Annotated[Session, Depends(get_session)]

def endpoint(session: SessionDep):
```

## SQLModel/SQLAlchemy Patterns

### Session Management

Always use context managers for sessions:
```python
with Session(engine) as session:
    # operations
    session.commit()
```

### Model Definitions

Use SQLModel's `Field()` for constraints:
```python
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None)
```

## Verification Checklist

Before writing Python code, verify:

- [ ] No deprecated FastAPI patterns (`on_event`, old dependency syntax)
- [ ] Using Python 3.10+ type syntax (`X | None` not `Optional[X]`)
- [ ] Pydantic V2 methods (`model_dump()` not `dict()`)
- [ ] Context managers for resources (files, sessions, connections)
- [ ] Async patterns where appropriate

## Scoring Rubric

| Score | Rating | Criteria |
|-------|--------|----------|
| 5/5 | Modern | All patterns current, no deprecated APIs |
| 4/5 | Good | 1-2 minor deprecated patterns |
| 3/5 | Adequate | Some deprecated patterns, core logic sound |
| 2/5 | Outdated | Multiple deprecated patterns throughout |
| 1/5 | Legacy | Predominantly old patterns, needs rewrite |

## Remediation Guide

| Deprecated Pattern | Fix | Search Regex |
|--------------------|-----|--------------|
| `@app.on_event` | Use `lifespan` context manager | `@app\.on_event` |
| `Optional[X]` | Replace with `X \| None` | `Optional\[` |
| `List[X]`, `Dict[K,V]` | Use `list[X]`, `dict[K,V]` | `List\[|Dict\[` |
| `.dict()` | Use `.model_dump()` | `\.dict\(\)` |
| `orm_mode = True` | Use `from_attributes = True` | `orm_mode` |
| `class Config:` | Use `model_config = ConfigDict(...)` | `class Config:` |

## References

For detailed patterns, see: `references/fastapi-patterns.md`
