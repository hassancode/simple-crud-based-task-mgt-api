"""
SQLModel Database Configuration Template

Copy this file to your project and customize:
1. Update DATABASE_URL for your database
2. Import your models before calling create_db_and_tables()
"""

from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# Database URL - customize for your database
# SQLite: "sqlite:///./database.db"
# PostgreSQL: "postgresql://user:password@localhost/dbname"
# MySQL: "mysql+pymysql://user:password@localhost/dbname"
DATABASE_URL = "sqlite:///./database.db"

# Create engine
# echo=True logs SQL queries (disable in production)
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}  # SQLite only
)


def create_db_and_tables():
    """Create all tables. Call after importing all models."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes."""
    with Session(engine) as session:
        yield session
