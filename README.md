# Task Management API

A simple CRUD-based task management API built with FastAPI and SQLModel.

## Tech Stack

- **FastAPI** - Web framework
- **SQLModel** - ORM (SQLAlchemy + Pydantic)
- **SQLite** - Database
- **uv** - Package manager
- **pytest** - Testing

## Setup

```bash
# Install dependencies
uv sync

# Run the server
uv run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/tasks` | Create a task |
| GET | `/tasks` | List all tasks |
| GET | `/tasks/{id}` | Get a task by ID |
| PUT | `/tasks/{id}` | Update a task |
| DELETE | `/tasks/{id}` | Delete a task |

## Task Schema

```json
{
  "id": 1,
  "title": "My task",
  "description": "Optional description",
  "completed": false
}
```

## Running Tests

```bash
uv run pytest
```

## API Documentation

Interactive docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Claude Code Skills

This project includes custom Claude Code skills in `.claude/skills/` to enhance AI-assisted development:

| Skill | Description |
|-------|-------------|
| **commit-and-push** | Commits changes using Conventional Commits format and pushes to remote. Handles git workflow with proper commit messages. |
| **fastapi-builder** | Scaffolds FastAPI applications with proper project structure, routes, Pydantic models, and database setup. Includes starter templates. |
| **pytest-fastapi** | Generates and runs tests for FastAPI apps. Supports TDD workflow with coverage analysis and test patterns. |
| **sqlmodel** | Database design using SQLModel (SQLAlchemy + Pydantic). Handles models, relationships, CRUD operations, and FastAPI integration. |
| **python-modern-practices** | Ensures Python code follows modern patterns (Python 3.10+, Pydantic V2, FastAPI lifespan). Prevents deprecated APIs. |
| **skill-creator** | Meta-skill for creating new Claude Code skills with proper structure, frontmatter, and bundled resources. |

### Using Skills

Skills are automatically triggered when Claude Code detects relevant context, or can be invoked manually:

```bash
# Example: commit changes
/commit-and-push

# Example: run tests
/pytest-fastapi
```
