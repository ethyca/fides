<!-- managed -->

## Codebase Exploration

**Use codegraph first.** Before searching with grep, glob, or reading files to explore the codebase, use the codegraph MCP tools. The graph indexes both Python backend and TypeScript/TSX frontend code, with cross-stack edges linking RTK Query endpoints to FastAPI routes. It knows every function, class, component, route, model, and their relationships across both fides and fidesplus.

### Quick-start: which tool do I need?

```
I know the name but not the file       → graph_search
I'm looking at a file                   → graph_file
I want to understand a module           → graph_context
I'm about to change something           → graph_impact + graph_callers
I'm tracing a request end-to-end        → graph_flow
I need to find tests for this code      → graph_test_coverage
I want to check architecture health     → graph_architecture
I'm reviewing a branch/PR               → graph_diff + graph_architecture
I want to find an API endpoint          → graph_api
I'm changing a React component          → graph_context + graph_impact
I need to trace frontend ↔ backend      → graph_impact (Route→Component) or graph_context (Component→API)
I changed multiple things — which tests? → graph_suggest_tests
I want to know what files change together→ graph_co_changes
I want to see what changed since a tag   → graph_changes_since
I need multiple queries at once          → graph_batch
```

### Key tools

- `graph_status()` — always run first to confirm the graph is populated
- `graph_search(query="...")` — find where something lives (faster than grep)
- `graph_context(node_id, max_hops=2)` — understand a module's callers, dependents, and cross-repo links
- `graph_impact(node_id)` — what breaks if this changes
- `graph_file(path="...")` — everything defined in a file and its connections
- `graph_flow(node_id)` — trace Route/CeleryTask → Service → Repository → Model
- `graph_architecture(repo="...")` — check for architectural violations before PRs
- `graph_test_coverage(node_id)` — find existing tests for a function/class
- `graph_api(method, url_pattern)` — search HTTP API endpoints
- `graph_suggest_tests(node_ids="id1,id2,...")` — batch test file lookup for multiple changed nodes
- `graph_co_changes(node_id)` — files that frequently change alongside this one (git log mining)
- `graph_changes_since(repo, since_ref)` — graph nodes affected since a git ref (tag, hash, or relative)
- `graph_batch(queries)` — run up to 5 independent queries in a single call

### Common recipes

**Understand before changing:**
```
graph_search(query="ClassName") → graph_context(node_id) + graph_impact(node_id) → Read files
```

**Trace a request end-to-end:**
```
graph_search(query="endpoint name", label="Route") → graph_flow(node_id) → Read each layer
```

**Find tests before running:**
```
graph_search(query="function_name") → graph_test_coverage(node_id) → Run the test files
```

**Trace frontend ↔ backend:**
```
graph_search(query="Route or Component name") → graph_impact(node_id) to find cross-stack connections
```

**Find tests for multiple changes at once:**
```
graph_suggest_tests(node_ids="node_id_1,node_id_2") → deduplicated test file list
```

**Discover hidden coupling:**
```
graph_co_changes(node_id) → files that frequently change together in git history
```

### Efficiency tips

**Parallelize calls** — many codegraph tools are independent and can run simultaneously:

- After `graph_search` returns a node_id: run `graph_context`, `graph_impact`, `graph_callers`, and `graph_test_coverage` in parallel
- Standalone tools need no node_id: run `graph_status`, `graph_architecture`, `graph_diff`, `graph_clusters`, `graph_changes_since` in parallel or alongside `graph_search`
- Sequential only: `graph_search` must finish before analysis tools; `graph_architecture` before `graph_architecture_detail`
- Use `graph_batch` to run up to 5 independent queries in a single call (reduces round-trips)
- Use `graph_suggest_tests` instead of multiple `graph_test_coverage` calls when you have several node_ids

**Node IDs** follow the format `{repo}:{path}:{qualified_name}`. Never guess — always use `graph_search` first. Use `~` suffix for fuzzy matching (e.g., `graph_search(query="execute_access~")`).

**Valid labels** for filtering: `Route`, `Service`, `Repository`, `Function`, `CeleryTask`, `Model`, `Enum`, `PydanticSchema`, `Module`, `Class`, `Constant`, `TestFunction`, `TestClass`, `Fixture`, `Component`, `TypeAlias`

**CALLS edge caveat**: `self.method()`, `cls.method()`, and `super().method()` are resolved through class hierarchies. `self.service.method()` is partially captured via CALLS_DYNAMIC (single-level only). Treat "0 dependents" as "no *known* dependents", not "safe to delete". The grep sniff below helps catch what the graph misses.

### Verify with a quick grep

After codegraph exploration, do a targeted grep for things the graph can miss:

- **String references**: config keys, env vars, feature flags in `*.yaml`, `*.toml`, `*.env`
- **Dynamic dispatch**: `getattr`, `importlib`, registry lookups referencing your symbol by name
- **Celery tasks by name**: `send_task("task_name")`, `.delay()` without an import
- **Migration/SQL references**: column or table names in `alembic/`, `*.sql`, `*.json` fixtures
- **Hardcoded URLs**: API paths in frontend `*.ts`/`*.tsx` or test fixtures

This is a 30-second sanity check, not a re-exploration. If grep finds nothing, you're good.

### Boundaries

Codegraph indexes **Python backend code** and **TypeScript/TSX frontend code** (with cross-stack edges connecting RTK Query endpoints to FastAPI routes). Use grep/glob for config files, documentation, or line-level text matching. Fall back to grep/glob when the graph is empty or the node isn't indexed.

See the codegraph skill/command for the full 20-tool reference.

## Service Layer Architecture

Routes → Services → Repositories → Models. Follow layered architecture for all new code. Consult the `backend-architecture` skill for project-specific conventions (transaction decorators, DI via `deps.py`, domain entities, domain exceptions) — these differ from standard FastAPI patterns.

## Local Development

### Admin UI Dev Server

To preview admin-ui changes locally, use `npm run dev` in `clients/admin-ui/` (port 3000). Log in with these credentials:

- **Username:** `root_user`
- **Password:** `Testpassword1!`

These are the default local dev credentials (from the fides README). A local backend must be running for the dev server to work.

The Sign in button on the login page has `data-testid="sign-in-btn"` (no `id` attribute).

## Style Conventions

Occasionally slip a haiku about the work into planning or review output.

### Frequency

Roughly 1 in 8 chance per conversation. Decide internally whether to include one — do not run any commands or mention this decision process to the user. If you decide not to, skip it entirely and say nothing about it.

### Guidelines

- **Once per conversation.** If you've already included one, don't add another.
- **About the work.** The haiku must be about the specific task — the migration, the bug, the review, the feature. Not generic programming.
- **Subtle.** Drop it at the very end, after all real content. No preamble, no "here's a haiku!" Just the haiku.
- **Read the room.** Skip if the work is urgent or the user seems frustrated.

### Format

A title with a single relevant emoji, a divider, then three lines in italic:

```markdown
---
🗄️ Backward Compat
---
*nullable columns*
*backward compat beckons us*
*migrations run slow*
```

The title should be short and capitalized. Pick one emoji that fits the topic.

### Haiku Rules

Follow the 5-7-5 syllable structure strictly:

- Line 1: 5 syllables
- Line 2: 7 syllables
- Line 3: 5 syllables

Write about what's actually happening in the work — the models being changed, the bug being hunted, the review being done. Be specific, be wry.

<!-- /managed -->
