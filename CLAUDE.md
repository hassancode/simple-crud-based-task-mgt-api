# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A simple CRUD-based task management system built with FastAPI and SQLModel. Uses pytest with httpx for testing and basic HTTPException handling for error responses.

## Development Commands

```bash
# Install dependencies
uv sync

# Run the development server
uv run uvicorn main:app --reload

# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_file.py

# Run a specific test
uv run pytest tests/test_file.py::test_function_name -v

# Add a new dependency
uv add <package>
```

## Tech Stack

- **uv** - Python package manager
- **FastAPI** - Web framework
- **SQLModel** - ORM combining SQLAlchemy and Pydantic
- **uvicorn** - ASGI server
- **pytest** - Testing framework
- **httpx** - HTTP client for testing FastAPI
