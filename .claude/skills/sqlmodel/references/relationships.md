# SQLModel Relationships

## Table of Contents
- [One-to-Many](#one-to-many)
- [Many-to-Many](#many-to-many)
- [One-to-One](#one-to-one)
- [Self-Referential](#self-referential)
- [Querying Relationships](#querying-relationships)

---

## One-to-Many

A user has many items. An item belongs to one user.

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Relationship: User has many Items
    items: List["Item"] = Relationship(back_populates="owner")


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float

    # Foreign key to User
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")

    # Relationship: Item belongs to User
    owner: Optional[User] = Relationship(back_populates="items")
```

### Usage
```python
# Create user with items
user = User(name="John")
item1 = Item(name="Laptop", price=999.99, owner=user)
item2 = Item(name="Phone", price=499.99, owner=user)

session.add(user)
session.commit()

# Query user's items
user = session.get(User, 1)
for item in user.items:
    print(f"{item.name}: ${item.price}")
```

---

## Many-to-Many

Users can have many roles. Roles can belong to many users.

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# Link table (association table)
class UserRoleLink(SQLModel, table=True):
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    role_id: Optional[int] = Field(
        default=None, foreign_key="role.id", primary_key=True
    )


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    roles: List["Role"] = Relationship(
        back_populates="users",
        link_model=UserRoleLink
    )


class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    users: List[User] = Relationship(
        back_populates="roles",
        link_model=UserRoleLink
    )
```

### Usage
```python
# Create roles
admin_role = Role(name="admin")
user_role = Role(name="user")

# Create user with roles
user = User(name="John", roles=[admin_role, user_role])

session.add(user)
session.commit()

# Query user's roles
user = session.get(User, 1)
for role in user.roles:
    print(role.name)  # admin, user
```

### Link Table with Extra Data
```python
class TeamMemberLink(SQLModel, table=True):
    team_id: Optional[int] = Field(
        default=None, foreign_key="team.id", primary_key=True
    )
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    # Extra fields on the relationship
    role: str = Field(default="member")  # member, lead, admin
    joined_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## One-to-One

A user has one profile. A profile belongs to one user.

```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    profile: Optional["Profile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )


class Profile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bio: str
    avatar_url: Optional[str] = None

    user_id: int = Field(foreign_key="user.id", unique=True)
    user: User = Relationship(back_populates="profile")
```

### Usage
```python
user = User(name="John")
profile = Profile(bio="Developer", user=user)

session.add(user)
session.commit()

# Access profile
user = session.get(User, 1)
print(user.profile.bio)  # Developer
```

---

## Self-Referential

For hierarchical data like categories, employees with managers, etc.

### Tree Structure (Parent-Child)
```python
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Parent reference
    parent_id: Optional[int] = Field(default=None, foreign_key="category.id")

    # Relationships
    parent: Optional["Category"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    children: List["Category"] = Relationship(back_populates="parent")
```

### Usage
```python
# Create category hierarchy
electronics = Category(name="Electronics")
phones = Category(name="Phones", parent=electronics)
laptops = Category(name="Laptops", parent=electronics)
iphones = Category(name="iPhones", parent=phones)

session.add(electronics)
session.commit()

# Navigate hierarchy
category = session.get(Category, 1)  # Electronics
for child in category.children:
    print(child.name)  # Phones, Laptops
```

### Employee-Manager
```python
class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    manager_id: Optional[int] = Field(default=None, foreign_key="employee.id")

    manager: Optional["Employee"] = Relationship(
        back_populates="reports",
        sa_relationship_kwargs={"remote_side": "Employee.id"}
    )
    reports: List["Employee"] = Relationship(back_populates="manager")
```

---

## Querying Relationships

### Eager Loading (Prevent N+1 Queries)
```python
from sqlmodel import select
from sqlalchemy.orm import selectinload

# Load user with items in single query
statement = select(User).options(selectinload(User.items))
users = session.exec(statement).all()

for user in users:
    for item in user.items:  # No additional query
        print(item.name)
```

### Join Queries
```python
from sqlmodel import select

# Get items with their owners
statement = select(Item, User).join(User)
results = session.exec(statement).all()

for item, user in results:
    print(f"{item.name} owned by {user.name}")

# Filter by relationship
statement = select(Item).join(User).where(User.name == "John")
johns_items = session.exec(statement).all()
```

### Filtering on Related Models
```python
# Users who have items priced over $500
statement = (
    select(User)
    .join(Item)
    .where(Item.price > 500)
    .distinct()
)
users = session.exec(statement).all()
```

---

## Common Patterns

### Soft Delete
```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None

# Soft delete
def soft_delete_user(session: Session, user_id: int):
    user = session.get(User, user_id)
    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    session.add(user)
    session.commit()

# Query only active users
statement = select(User).where(User.is_deleted == False)
```

### Timestamps Mixin
```python
class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )

class User(TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
```

### Cascade Delete
```python
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    items: List["Item"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```
