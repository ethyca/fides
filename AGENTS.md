# 🔒 CRITICAL: Public Repository Security - Zero Tolerance for Sensitive Information

This is a **PUBLIC OSS repository**. Any customer or internal sensitive information committed here is immediately visible to the entire world and permanently recorded in git history.

## 🚨 IMMEDIATE THREATS

### 1. Slack Background Agent Context Exposure
Background Agents import ENTIRE Slack thread context when creating PRs. Slack threads frequently contain:
- **Customer identifiers**: Real company names, contact details, domain names
- **Internal systems**: Server names, database hosts, internal URLs, staging environments
- **Personnel information**: Employee names, email addresses, Slack handles
- **Sensitive data**: Customer logs, error messages, configuration values, API responses
- **Business context**: Support tickets, customer issues, internal processes

### 2. Copy-Paste from Internal Tools
Common sources of accidental disclosure:
- Pasting error logs from production systems
- Copying configuration examples from internal documentation
- Including actual database queries with real table/column names
- Sharing screenshots with sensitive information visible

## 🛡️ MANDATORY PRE-COMMIT CHECKLIST

Before ANY commit, verify ZERO instances of:

### Customer Information
- [ ] Real company/organization names (beyond generic examples)
- [ ] Actual email addresses (use `user@example.com`, `admin@test.invalid`)
- [ ] Customer domain names (use `customer.example`, `client.test`)
- [ ] Production database/table names (use `customer_db`, `user_table`)
- [ ] Support ticket references (use generic issue descriptions)
- [ ] Customer-specific configuration values or API responses

### Internal Ethyca Information
- [ ] Employee names or Slack handles in code/comments
- [ ] Internal URLs (`*.ethyca.com`, staging environments)
- [ ] Internal system names (servers, databases, services)
- [ ] Private API keys/tokens (even fake-looking ones)
- [ ] Internal Jira/ticket numbers
- [ ] Proprietary business logic or processes

### Contextual References
- [ ] Slack conversation excerpts or references
- [ ] Internal meeting notes or decisions
- [ ] Customer-specific debugging context
- [ ] References to internal documentation or tools

## ✅ APPROVED ALTERNATIVES

### Safe Placeholder Patterns
```
# Companies
customer_corp, acme_inc, example_org, test_company

# Emails
user@example.com, admin@test.invalid, contact@customer.example

# URLs
https://api.example.com, https://customer.test, https://client.invalid

# Database names
customer_db, user_data, application_store, test_database

# API keys (clearly marked)
sk_test_1234567890abcdef (example only), api_key_placeholder
```

### Generic Descriptions
```
❌ "Fix validation issue for ACME Corp's user import"
✅ "Fix validation issue in bulk user import feature"

❌ "Handle edge case found in customer ticket #12345"
✅ "Handle edge case in date parsing validation"

❌ "Update config for staging.internal.ethyca.com"
✅ "Update configuration template for deployment environments"
```

## 📋 FILE TYPE SPECIFIC GUIDELINES

### Source Code
- Use generic variable names: `customer_config`, `client_data`, `organization_settings`
- Generic error messages: `"Invalid configuration format"` not `"Invalid format in ACME Corp config"`
- Generic function names: `validate_customer_data()` not `validate_acme_data()`

### Test Files
- Generate completely fictional test data
- Use RFC 2606 reserved domains or subdomains: `.example`, `subdomain.example.com`
- Fake but realistic data structures
- No real customer data patterns or schema

### Configuration Files
- Template configurations only, never actual values
- Use environment variable placeholders: `${DATABASE_URL}`, `${API_KEY}`
- Example endpoints using reserved domains
- Generic service names and identifiers

### Documentation
- Generic use cases and examples
- Link to public documentation only
- Describe patterns, not specific implementations
- Use "customer", "organization", "user" instead of real names

### Database Migrations/Scripts
- Generic table/column names that don't mirror customer schemas
- Example data that's clearly fictional
- No references to production system structures
- Generic constraint and index names

## 🚩 AUTOMATIC RED FLAGS

Stop immediately if you see:
- Email addresses not ending in `.example/.invalid/.example.com`
- URLs containing real domain names (except public documentation)
- Any `.com/.org/.net` domains that aren't reserved examples
- Names that could be real people/companies
- API keys that look production-ready
- Internal-looking system names or server references
- Specific numeric identifiers that could be real tickets/IDs

## 🔍 VERIFICATION PROCESS

### Before Committing
1. **Search your changes** for company names, email patterns, URL patterns
2. **Review context**: Does any code comment reference specific customers or incidents?
3. **Check test data**: Is all test data clearly fictional?
4. **Validate examples**: Are configuration examples using reserved domains?

### Background Agent PR Reviews
- **Never directly copy Slack content** into commit messages or PR descriptions
- **Rewrite in generic terms**: Focus on the technical change, not business context
- **Strip customer context**: Remove all references to specific customers or incidents
- **Generic PR titles**: "Fix data validation issue" not "Fix validation for customer X"

## 🎯 SUCCESS METRICS

- Zero customer/internal information in public commits
- All test data clearly fictional and generic
- All configuration examples use reserved domains
- All error messages and logs are sanitized of customer context
- Background Agent PRs contain no Slack context

**Remember**: Once committed to this public repository, information is permanently visible to the world and recorded in git history. When in doubt, use generic alternatives.

## Cursor Cloud specific instructions

### Architecture overview

Fides is a privacy engineering platform with:
- **Backend**: Python 3.13 / FastAPI API server (port 8080) with Celery workers
- **Frontend**: Next.js monorepo under `clients/` (Admin UI on port 3000, Privacy Center on port 3001, fides-js SDK, fidesui component library)
- **Infrastructure**: PostgreSQL 16 (port 5432), Redis 8.0 (port 6379)

### Running the dev environment

The standard dev workflow uses Docker via `nox -s dev`. For cloud agents, use Docker Compose directly:

1. **Start infrastructure**: `docker compose up -d fides-db redis`
2. **Start Fides API**: `docker compose up -d fides` (uses `ethyca/fides:local` image)
3. **Start Admin UI locally** (for testing): `cd clients && NEXT_PUBLIC_FIDESCTL_API_SERVER=http://localhost:8080 npm run dev-admin-ui`

The Docker dev image is tagged `ethyca/fides:local`. If the local Docker build fails (e.g., due to transient `virtualenv`/`hatch` compatibility issues), use `docker pull ethyca/fides:dev && docker tag ethyca/fides:dev ethyca/fides:local` as a workaround.

Default credentials: username `root_user`, password `Testpassword1!`.

### Running linting and checks

- **Python lint**: `uv run ruff check src/`
- **Python format**: `uv run ruff format --check src/`
- **Python type check**: `uv run mypy src/`
- **Frontend lint**: `cd clients && npm run lint`
- **Frontend typecheck**: `cd clients && npm run typecheck` (requires `fides-js` to be built first: `npm run build -w fides-js`)

### Running tests locally (outside Docker)

When running pytest outside Docker, set these env vars to point to the Docker-hosted Postgres/Redis:

```
export FIDES__DATABASE__SERVER="127.0.0.1"
export FIDES__DATABASE__PASSWORD="fides"
export FIDES__REDIS__HOST="127.0.0.1"
export FIDES__REDIS__PASSWORD="redispassword"
export FIDES__TEST_MODE="true"
unset FIDES__CONFIG_PATH
```

Then run: `uv run pytest tests/lib/ -m "unit"` (see `scripts/run_lib_tests.sh` for reference).

### Gotchas

- The `fides-js` workspace package must be built (`npm run build -w fides-js`) before `privacy-center` typecheck will pass, since it generates type declarations.
- The `.env` file is auto-created from `example.env` by `noxfile.py` if missing. For direct Docker Compose usage, copy it manually: `cp example.env .env`.
- The `docker-compose.yml` expects the `.env` file to exist (referenced via `env_file`).
- The `pymssql` optional dependency requires `freetds-dev` system package to build.
- Some ctl unit tests (e.g., `test_view_credentials`) expect a credentials file at `~/.fides_credentials` and will fail without it; this is expected when running outside the Docker container.
- The noxfile startup checks require Docker >= 20.10.17 and Python 3.13.
