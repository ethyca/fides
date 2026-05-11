# Lethe

Postgres-backed **DSR state** (`DSRStore`) lives here. This package is the home for DSR persistence that used to be split across Redis “cache” keys and ad-hoc helpers.

## Dependency-direction policy

`lethe.state` should stay a thin persistence facade. It may import infrastructural fides modules (`fides.api.db.base_class`, `fides.config`, etc.). `DSRStore` resolves ORM rows via lazy imports from `fides.api.models.*` **inside methods** to avoid import cycles; keep that pattern—do not grow new upward dependencies into services or HTTP layers.

`lethe.migration` is **exempt** from the strict state-only rule: one-off tooling may import `fides.api.util.cache`, models, and `get_db_session` to read legacy Redis keys and write Postgres.

Third-party imports (SQLAlchemy, Pydantic, etc.) are unrestricted.

## Session injection

`lethe.state.DSRStore` always takes a SQLAlchemy `Session` in its constructor. Lethe never creates an engine, never owns a sessionmaker, and never opens a connection. Callers own transaction boundaries (`commit` / `rollback`). The store may `flush()` so writes are visible inside the caller’s transaction, but it must not call `commit()` or `rollback()`.

## Offline migration (legacy Redis → Postgres)

After deploying the Postgres columns, run:

`fides db migrate-dsr-redis`

Options:

- `--dry-run` — log planned writes, no commits
- `--force` — overwrite non-empty columns when Redis still has data
- `--limit N` — cap how many privacy request ids are processed (sorted)

This copies best-effort fields (encryption key, merged DRP attrs, async task id, retry count). It does **not** move identities or masking secrets.

## CI boundary check

`nox -s check_lethe_boundary` (also wired into `static_checks`) runs `scripts/check_lethe_state_boundary.py` to ensure `src/lethe/state` does not import Redis clients, call `commit`/`rollback`, or reach for `get_cache()`.

## Adding a new model

Register new SQLAlchemy table classes on shared metadata by adding an explicit import in `fides.api.alembic.migrations.env` (e.g. `import lethe.state.models  # noqa: F401`) so Alembic/autogenerate and runtime metadata stay aligned.
