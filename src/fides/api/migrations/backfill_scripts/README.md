# Backfill Scripts

This directory contains backfill scripts for data migrations that are deferred from standard Alembic migrations due to table size.

## When to Use

Use a backfill script when:
- The table is large enough that an UPDATE would cause long-running transactions
- You need batched processing with delays to minimize lock contention

## Creating a Backfill

1. **Create the backfill script** in this directory (e.g., `backfill_my_table_my_column.py`):

```python
from sqlalchemy import text
from sqlalchemy.orm import Session
from fides.api.migrations.backfill_scripts.utils import batched_backfill

def get_pending_count(db: Session) -> int:
    result = db.execute(text("SELECT COUNT(*) FROM my_table WHERE my_column IS NULL"))
    return result.scalar() or 0

@batched_backfill(
    name="my_table-my_column",
    pending_count_fn=get_pending_count,
)
def backfill_my_column(db: Session, batch_size: int) -> int:
    result = db.execute(text("""
        UPDATE my_table SET my_column = 'value'
        WHERE id IN (
            SELECT id FROM my_table WHERE my_column IS NULL
            LIMIT :batch_size FOR UPDATE SKIP LOCKED
        )
    """), {"batch_size": batch_size})
    db.commit()
    return result.rowcount
```

2. **Register the backfill** in `post_upgrade_backfill.py`:

```python
from fides.api.migrations.backfill_scripts.backfill_my_column import backfill_my_column

def run_all_backfills(...):
    results.append(backfill_my_column(db, batch_size, batch_delay_seconds))
```

3. **Update the migration's downgrade()** to clear backfill tracking:

```python
def downgrade():
    op.drop_column("my_table", "my_column")
    op.execute("DELETE FROM backfill_history WHERE backfill_name = 'my_table-my_column'")
```

This ensures the backfill re-runs if the migration is rolled back and re-applied.

4. **Update the status endpoint** in `api/v1/endpoints/admin.py` to include the pending count:

```python
pending_count={
    "my_table-my_column": get_pending_my_column_count(db),
}
```

> **Note**: This manual step could be improved by auto-registering backfills in the decorator. For now, remember to update both `post_upgrade_backfill.py` and `admin.py` when adding a new backfill.

## How It Works

- Backfills run automatically at startup via the scheduler
- Uses Redis lock to prevent concurrent execution
- Tracks completed backfills in `backfill_history` table to prevent re-execution
- Processes in batches with delays to minimize database impact

## Why Track Completed Backfills?

Checking pending rows alone is not enough. Consider this scenario:

1. Backfill runs and completes successfully
2. Backfill code remains in codebase (not removed)
3. Later, business logic changes - now some rows can have NULL intentionally
4. New rows are added with NULL values (by design)
5. Old backfill detects NULL rows and overwrites them - **unintended behavior**

The `backfill_history` table prevents this by marking a backfill as "done" permanently, regardless of future data changes.

## API Endpoints

If a backfill fails or you need to run it manually:

- **`POST /api/v1/admin/backfill`** - Runs all pending backfills (those not yet in `backfill_history`)
- **`GET /api/v1/admin/backfill`** - Check backfill status and pending row counts

Both endpoints require the `BACKFILL_EXEC` scope.
