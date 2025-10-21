# DB Session Management Best Practices

## General Principles

As outlined in the [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it):

- Keep the lifecycle of the session separate and external from functions and objects that access and/or manipulate database data. This will greatly help with achieving a predictable and consistent transactional scope.

- Make sure you have a clear notion of where transactions begin and end, and keep transactions short, meaning, they end at the series of a sequence of operations, instead of being held open indefinitely.

## Key Concepts

### Sessions vs. Transactions

[Section to be expanded with details about the differences between sessions and transactions]

### Sync vs. Async Session

[Section to be expanded with details about synchronous and asynchronous session handling]

## In Practice

### Rules of Thumb

| Location | Session Lifecycle | Transaction Lifecycle | Notes |
|----------|------------------|----------------------|--------|
| Endpoint function | Managed by FastAPI dependency injection | Managed by FastAPI dependency injection | Use `get_db()` or `get_async_db()` dependencies |
| Worker task | [To be defined] | [To be defined] | [Additional guidance needed] |

### What to Use

[reference generators that provide our standard sessionmaker objects]

### Examples
