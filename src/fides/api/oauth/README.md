# Permission Checker — Dependency Injection Pattern

## Why This Refactor Was Needed

The original `rbac-api` branch introduced a global callback (`_custom_permission_checker`)
to let fidesplus override permission checking logic. A code review identified several
bugs and design issues that warranted a structural fix before merge.

## Bugs in the Original Callback Implementation

### 1. Async path silently broken

`verify_oauth_client_async` never passed `db` to `has_permissions()`, so the custom
RBAC checker would receive `db=None` and fail at runtime for any async endpoint.

### 2. No composition

When the callback was set, it **fully replaced** the default `_has_direct_scopes` +
`_has_scope_via_role` logic. The custom checker had to reimplement root client handling,
direct scope checks, and role resolution from scratch. A bug in any of those areas would
break all authorization.

### 3. `db=None` time bomb

`has_permissions` accepted `db: Optional[Session] = None`. Callers that forgot to pass
`db` would silently send `None` to the RBAC checker, which would fail only at query time
with an opaque error.

### 4. Silent replacement

Calling `register_permission_checker()` twice silently replaced the first checker with no
warning or error.

### 5. Test state leakage

A test that registered a checker and failed before calling `clear_permission_checker()`
would leak the custom checker into subsequent tests, causing cascading failures.

## The DI Pattern

Permission checking is now provided via a FastAPI dependency:

```python
def get_permission_checker() -> PermissionCheckerCallback:
    """Override via app.dependency_overrides[get_permission_checker]."""
    return default_has_permissions
```

All functions that check permissions receive the checker as an explicit argument — either
injected by FastAPI via `Depends(get_permission_checker)` or passed directly as a
parameter with `default_has_permissions` as the default.

### Dependency flow

```
get_permission_checker()                       [sync]
    │
    ├── verify_oauth_client          (Depends)
    ├── verify_user_read_scopes      (Depends)
    ├── get_current_user             (Depends)
    │
    ├── has_permissions()            (parameter, default=default_has_permissions)
    ├── has_system_permissions()     (parameter, default=default_has_permissions)
    └── verify_client_can_assign_scopes()  (parameter, default=default_has_permissions)

get_async_permission_checker()                 [async]
    │
    └── verify_oauth_client_async    (Depends)
```

`copy_func` variants (`verify_oauth_client_prod`, `verify_oauth_client_plus`,
`verify_oauth_client_plus_async`) inherit the `Depends` default from their source
function, so they also participate in the override mechanism.

## How Fidesplus Hooks In

Two lines in `main.py`:

```python
fides.dependency_overrides[get_permission_checker] = get_rbac_permission_checker
fides.dependency_overrides[get_async_permission_checker] = get_rbac_permission_checker_async
```

This follows the exact same pattern already used for:

- `verify_oauth_client_prod` → `get_root_client` (dev-mode auth bypass)
- `verify_oauth_client_plus` → `get_root_client` (dev-mode auth bypass)

The RBAC checker can call `default_has_permissions()` internally to compose with the
default logic rather than replacing it entirely.

## Async vs Sync Checkers

The sync and async permission checkers are separate dependencies, following the same
pattern as `get_db` / `get_async_db` and `verify_oauth_client` /
`verify_oauth_client_async`:

| Sync | Async |
|------|-------|
| `PermissionCheckerCallback` | `AsyncPermissionCheckerCallback` |
| `default_has_permissions` | `default_has_permissions_async` |
| `get_permission_checker()` | `get_async_permission_checker()` |
| Receives `Optional[Session]` | Receives `Optional[AsyncSession]` |

The default async checker delegates to the sync default (since the built-in logic doesn't
use the database). Custom async checkers (e.g., RBAC) receive the real `AsyncSession` and
can perform async database queries directly.
