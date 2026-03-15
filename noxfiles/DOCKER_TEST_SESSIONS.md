# Docker test sessions: service required vs pytest-only

This doc classifies nox sessions that run inside Docker by whether they **need the Fides service (webserver) to be running** or only need to **run a command (e.g. pytest) inside the image**.

## Sessions that only run pytest in the image (service does **not** need to be running)

These sessions currently use `START_APP` (docker compose up --wait) then `EXEC` (docker exec ... pytest). They do **not** run `LOGIN` and their tests do not depend on the HTTP API being up. They could be changed to use `RUN` (docker compose run fides pytest ...) so the service is never started and the healthcheck is not waited on.

| Test group       | Session / function   | Notes                          |
|------------------|----------------------|--------------------------------|
| **lib**          | `pytest_lib`         | tests/lib/; no LOGIN           |
| **ops-unit-api** | `pytest_ops(unit, api)` | ops unit tests (api dir); no LOGIN |
| **ops-unit-non-api** | `pytest_ops(unit, non-api)` | ops unit tests (non-api); no LOGIN |
| **misc-unit**    | `pytest_misc_unit`   | service/task/util unit tests; no LOGIN |

**Note:** There is no **ops-unit** (generic) in the Safe-Tests matrix; the workflow runs **ops-unit-api** and **ops-unit-non-api** separately. The generic **ops-unit** session would also be pytest-only (no LOGIN) if added.

## Sessions that need the service running

These either run `LOGIN` (which hits the API) or run tests that call the running server.

| Test group / session | Reason |
|----------------------|--------|
| **ctl-unit**, **ctl-not-external**, **ctl-integration**, **ctl-external** | All run `LOGIN` (fides user login) before pytest; API must be up. |
| **api** | API tests use `config.cli.server_url` and hit the running Fides server. |
| **ops-integration** | `run_infrastructure()` does `up --wait` then runs pytest; integration tests need full stack. |
| **ops-external-datastores**, **ops-saas** | START_APP (or with external Postgres) then EXEC; integration tests need app and DB. |
| **misc-integration**, **misc-integration-external** | START_APP and/or run_infrastructure; need full stack. |
| **fides_db_scan** (Misc-Tests) | START_APP then exec `fides scan`; needs app and DB. |
| **minimal_config_startup** (Misc-Tests) | Explicitly tests that the service starts (compose up --wait). |
| **check_container_startup**, **check_worker_startup** | Explicitly test service/worker startup. |

## Sessions that don’t use the main app container

| Session | How it runs |
|---------|-------------|
| **check_fides_annotations** (Misc-Tests) | `RUN_NO_DEPS` (one-off container: `fides evaluate`); no service needed. |
| **docs_check** | Builds and runs the docs image; separate from main Fides service. |
| **nox** (pytest nox) | Runs on host in nox venv; no Docker. |

## Possible optimization

For **lib**, **ops-unit-api**, **ops-unit-non-api**, and **misc-unit**, the nox flow could be changed from:

- `session.run(*START_APP, external=True)` then `session.run(*EXEC, "pytest", ..., external=True)`

to:

- `session.run(*RUN, "pytest", ..., external=True)`  (with appropriate env and args)

so that:

- The stack is brought up only as needed for the one-off `pytest` run (compose still starts dependencies like Postgres/Redis for the `fides` service).
- The Fides service healthcheck is never waited on, which can save time in CI.

The same image is still required; only the way the container is used (run vs up + exec) would change.
