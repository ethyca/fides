# DB Session Management Best Practices

## General Principles

As outlined in the [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it):

- Keep the lifecycle of the session separate and external from functions and objects that access and/or manipulate database data. This will greatly help with achieving a predictable and consistent transactional scope.

- Make sure you have a clear notion of where transactions begin and end, and keep transactions short, meaning, they end at the series of a sequence of operations, instead of being held open indefinitely.

## Key Concepts

### Sessions vs. Transactions

A **Session** is SQLAlchemy's "holding zone" for all ORM-mapped objects. It:
- Provides identity map (tracks objects by primary key)
- Manages connection checkout from the pool
- Coordinates write operations

A **Transaction** is the actual database transaction that:
- Begins when you first interact with the database via the session
- Ends on `commit()` or `rollback()`
- Can be nested (savepoints) within a session

Key distinction: A session may span multiple transactions, but each transaction is tied to a single session. In practice, keep both short-lived.

### Sync vs. Async Session

**Synchronous Sessions** (`sync_session`, `get_db()`, `get_api_session()`):
- Block the thread while waiting for database operations
- Use in Celery tasks, synchronous code paths, and blocking contexts
- Created via `sessionmaker(engine, class_=ExtendedSession)`

**Asynchronous Sessions** (`async_session`, `get_async_db()`):
- Non-blocking, await-based database operations
- Use in FastAPI async endpoints and async service methods
- Created via `sessionmaker(async_engine, class_=AsyncSession)`

Both types support context manager usage (`with`/`async with`) for automatic cleanup.

## In Practice

### Rules of Thumb

| Location | Session Lifecycle | Transaction Lifecycle | Notes |
|----------|------------------|----------------------|--------|
| Endpoint function | Managed by FastAPI dependency injection | Managed by FastAPI dependency injection | Use `get_db()` or `get_async_db()` dependencies |
| Worker task (Celery) | Use `DatabaseTask.get_new_session()` context manager | Keep transactions short; commit after each logical unit | Get fresh sessions per operation; don't hold sessions during long-running external calls |
| Repository method | `async_session()` / `sync_session()` context manager | Commit within the context manager block | Repository owns session lifecycle |
| Standalone/initialization code | `get_autoclose_db_session()` context manager | Commit explicitly within context | For code outside request/task context |

### What to Use

| Context | Sync | Async |
|---------|------|-------|
| FastAPI dependency | `get_db()` | `get_async_db()` |
| Repository (self-managed) | `sync_session()` from `fides.api.db.ctl_session` | `async_session()` from `fides.api.db.ctl_session` |
| Celery task | `self.get_new_session()` from `DatabaseTask` | N/A (Celery is synchronous) |
| Manual context (startup, scripts) | `get_autoclose_db_session()` from `fides.api.api.deps` | `get_async_autoclose_db_session()` from `fides.api.api.deps` |

## The Repository Pattern

The repository pattern provides a clean separation between database operations and business logic. Key characteristics:

### Session Ownership

Repositories manage their own sessions internally. Each public method:
1. Opens a session (via context manager)
2. Executes database operations
3. Commits the transaction
4. Closes the session
5. Returns domain entities (not ORM objects)

```python
from fides.api.db.ctl_session import async_session, sync_session

class MyRepository:
    """Repository manages its own session lifecycle."""

    async def get_by_id(self, entity_id: str) -> Optional[MyEntity]:
        """Each method opens and closes its own session."""
        async with async_session() as session:
            result = await session.execute(
                select(MyModel).where(MyModel.id == entity_id)
            )
            orm_obj = result.scalar_one_or_none()
            if orm_obj is None:
                return None
            # Convert to domain entity before session closes
            return MyEntity.from_orm(orm_obj)

    def get_by_id_sync(self, entity_id: str) -> Optional[MyEntity]:
        """Sync version for Celery tasks."""
        with sync_session() as session:
            result = session.execute(
                select(MyModel).where(MyModel.id == entity_id)
            )
            orm_obj = result.scalar_one_or_none()
            if orm_obj is None:
                return None
            return MyEntity.from_orm(orm_obj)
```

### Sync and Async Pairs

Repositories often provide both sync and async versions of methods:
- **Async methods** (e.g., `get_latest()`, `create()`): Used in FastAPI async endpoints
- **Sync methods** (e.g., `get_latest_sync()`, `create_sync()`): Used in Celery tasks

```python
class PrivacyPreferencesRepository:
    async def create(self, entity: Entity) -> Entity:
        """For use in async contexts (FastAPI endpoints)."""
        async with async_session() as session:
            # ... create logic ...
            await session.commit()
            return Entity.from_orm(orm_obj)

    def create_sync(self, entity: Entity) -> Entity:
        """For use in sync contexts (Celery tasks)."""
        with sync_session() as session:
            # ... same logic, sync version ...
            session.commit()
            return Entity.from_orm(orm_obj)
```

### Service Layer Benefits

With repositories managing sessions, the service layer remains database-agnostic:

```python
class MyService:
    def __init__(self, repository: Optional[MyRepository] = None):
        self.repository = repository or MyRepository()

    async def process(self, data: InputData) -> OutputData:
        # Service focuses on business logic
        # No session management needed!
        existing = await self.repository.get_by_id(data.id)
        if existing:
            return await self.repository.update(existing, data)
        return await self.repository.create(data)
```

## Anti-Patterns and Common Issues

### ❌ Holding Sessions During Long Operations

**Problem**: Holding a session during a long-running operation (e.g., external API calls, LLM inference) leads to connection timeouts.

```python
# BAD: Session held for 30+ minutes
def classify_resources(self, db: Session):
    resources = db.query(Resource).all()  # Session opened

    results = llm_service.classify(resources)  # Takes 30 minutes!

    # Connection may be dead by now
    for r in resources:
        r.classification = results[r.id]  # ❌ psycopg2.OperationalError
    db.commit()
```

**Solution**: Close session before long operations, reopen after:

```python
# GOOD: Short-lived sessions
def classify_resources(self):
    with sync_session() as session:
        resources = session.execute(select(Resource)).scalars().all()
        resource_data = [r.to_dict() for r in resources]  # Extract data
        session.expunge_all()  # Detach objects

    # Session closed, connection returned to pool
    results = llm_service.classify(resource_data)  # Takes 30 minutes

    # Fresh session with fresh connection
    with sync_session() as session:
        self._apply_results(session, results)
        session.commit()
```

### ❌ Returning ORM Objects from Repositories

**Problem**: ORM objects become detached when the session closes, causing `DetachedInstanceError` on attribute access.

```python
# BAD: Returns ORM object
def get_user(self) -> User:  # User is an ORM model
    with sync_session() as session:
        return session.query(User).first()  # ❌ Detached after context exits

# Later...
user = repo.get_user()
print(user.email)  # ❌ DetachedInstanceError
```

**Solution**: Convert to domain entities before closing session:

```python
# GOOD: Returns domain entity
def get_user(self) -> Optional[UserEntity]:
    with sync_session() as session:
        orm_obj = session.query(User).first()
        if orm_obj is None:
            return None
        return UserEntity.from_orm(orm_obj)  # ✅ Plain Python object
```

### ❌ Session Per Request Held Too Long

**Problem**: FastAPI dependency injection holds the session for the entire request duration.

```python
# Potentially problematic for long requests
@router.post("/process")
async def process(db: Session = Depends(get_db)):
    data = await external_service.fetch()  # Long operation with session held
    # ... more processing ...
```

**Solution**: For long-running operations within endpoints, use repository pattern or explicit session management:

```python
@router.post("/process")
async def process():
    # Let repository handle its own short-lived sessions
    data = await my_service.process()  # Service uses repository internally
    return data
```

### ❌ Mixing Session Sources

**Problem**: Using multiple session sources in a single operation breaks transaction isolation.

```python
# BAD: Two different sessions
def transfer(self, db: Session):  # Injected session
    with sync_session() as other_session:  # Different session!
        # Operations on db and other_session are NOT in same transaction
        source = db.query(Account).get(1)
        dest = other_session.query(Account).get(2)  # ❌ Different session
```

**Solution**: Use a single session for related operations, or use proper saga/outbox patterns for distributed transactions.

## Examples

### FastAPI Endpoint (Dependency Injection)

```python
from fides.api.api.deps import get_db

@router.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Session managed by FastAPI DI."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    return user
```

### Celery Task (DatabaseTask)

```python
from fides.api.tasks import DatabaseTask, celery_app

@celery_app.task(base=DatabaseTask, bind=True)
def process_items(self: DatabaseTask, item_ids: list[str]):
    """Use get_new_session() for each database operation."""
    for item_id in item_ids:
        with self.get_new_session() as session:
            item = session.query(Item).get(item_id)
            item.processed = True
            session.commit()
        # Session closed - connection returned to pool

        external_api.notify(item_id)  # Safe to call external service
```

### Repository Pattern (Full Example)

```python
from fides.api.db.ctl_session import async_session, sync_session

class UserRepository:
    """Repository with self-managed sessions."""

    async def create(self, user_data: UserCreate) -> UserEntity:
        async with async_session() as session:
            user = User(**user_data.model_dump())
            session.add(user)
            await session.flush()  # Get generated ID
            await session.refresh(user)  # Load defaults
            entity = UserEntity.from_orm(user)
            await session.commit()
            return entity

    async def update(self, user_id: str, updates: UserUpdate) -> UserEntity:
        async with async_session() as session:
            user = (await session.execute(
                select(User).where(User.id == user_id)
            )).scalar_one()
            for key, value in updates.model_dump(exclude_unset=True).items():
                setattr(user, key, value)
            await session.flush()
            entity = UserEntity.from_orm(user)
            await session.commit()
            return entity

    def create_sync(self, user_data: UserCreate) -> UserEntity:
        """Sync version for Celery tasks."""
        with sync_session() as session:
            user = User(**user_data.model_dump())
            session.add(user)
            session.flush()
            session.refresh(user)
            entity = UserEntity.from_orm(user)
            session.commit()
            return entity
```

### Startup/Initialization Code

```python
from fides.api.api.deps import get_autoclose_db_session

def initialize_system():
    """Use context manager for explicit session control."""
    with get_autoclose_db_session() as db:
        config = db.query(SystemConfig).first()
        if not config:
            config = SystemConfig(initialized=True)
            db.add(config)
            db.commit()
    # Session automatically closed
```
