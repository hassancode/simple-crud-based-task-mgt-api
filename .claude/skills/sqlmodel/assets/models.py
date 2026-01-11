"""
SQLModel Models Template

Common patterns for SQLModel database models.
Customize and expand based on your needs.
"""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


# =============================================================================
# Mixins (inherit from these for common fields)
# =============================================================================

class TimestampMixin(SQLModel):
    """Add created_at and updated_at to any model."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )


# =============================================================================
# Base/Read/Create Pattern
# =============================================================================

class UserBase(SQLModel):
    """Shared fields for User."""
    email: str = Field(unique=True, index=True)
    name: str
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    """Fields for creating a user (no id, includes password)."""
    password: str


class UserRead(UserBase):
    """Fields returned from API (has id, no password)."""
    id: int


class UserUpdate(SQLModel):
    """Fields for updating (all optional)."""
    email: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase, TimestampMixin, table=True):
    """Database table model."""
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    # Relationship: User has many Items
    items: List["Item"] = Relationship(back_populates="owner")


# =============================================================================
# Related Model (One-to-Many)
# =============================================================================

class ItemBase(SQLModel):
    """Shared fields for Item."""
    name: str = Field(index=True)
    description: Optional[str] = None
    price: float = Field(ge=0)


class ItemCreate(ItemBase):
    """Fields for creating an item."""
    pass


class ItemRead(ItemBase):
    """Fields returned from API."""
    id: int
    owner_id: int


class Item(ItemBase, TimestampMixin, table=True):
    """Database table model."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Foreign key to User
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Relationship: Item belongs to User
    owner: Optional[User] = Relationship(back_populates="items")
