# Async Database Connection Pool Optimization Guide

This guide explains how to configure and optimize the asynchronous read-only database connection pool for high-performance scenarios. These optimizations are particularly important for production deployments expecting high traffic volumes.

## Overview

Fides uses [SQLAlchemy 1.4](https://docs.sqlalchemy.org/en/14/) with [asyncpg](https://magicstack.github.io/asyncpg/) for asynchronous database operations. The async read-only connection pool can be pre-warmed and configured to skip expensive rollback operations, resulting in significant performance improvements under load.

### Related SQLAlchemy Documentation

- [Connection Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html) - Comprehensive guide to SQLAlchemy connection pooling
- [QueuePool](https://docs.sqlalchemy.org/en/14/core/pooling.html#sqlalchemy.pool.QueuePool) - The pool implementation used by Fides (wrapped for async)
- [Engine Configuration](https://docs.sqlalchemy.org/en/14/core/engines.html) - create_engine() and create_async_engine() parameters

## ⚠️ Important: External Connection Pooling Strongly Recommended

**For production deployments, it is strongly recommended to use an external database connection pooling technology** such as:

- [**PgBouncer**](https://www.pgbouncer.org/) - Lightweight connection pooler for PostgreSQL
- [**AWS RDS Proxy**](https://aws.amazon.com/rds/proxy/) - Managed connection pooler for AWS RDS/Aurora
- [**Azure Database for PostgreSQL built-in pooling**](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-pgbouncer)
- [**Google Cloud SQL Auth Proxy**](https://cloud.google.com/sql/docs/postgres/sql-proxy) with connection pooling
- [**Odyssey**](https://github.com/yandex/odyssey) - Advanced multi-threaded PostgreSQL connection pooler

### Why External Pooling?

PostgreSQL uses a **process-per-connection model**, where each connection spawns a separate backend process. This architecture has important implications:

1. **High Memory Overhead**: Each PostgreSQL backend process consumes significant memory (typically 10-20MB base + working memory). With hundreds of connections across multiple Fides workers, this can quickly exhaust database server memory.

2. **Connection Establishment Cost**: Creating new PostgreSQL connections involves process forking, authentication, and initialization. While pre-warming helps on the application side, it doesn't solve the database-side resource consumption.

3. **Scaling Challenges**: Modern cloud deployments often run multiple pods/containers/workers. If each worker maintains a pool of 300 connections, and you have 10 workers, that's 3,000 database connections - far exceeding typical PostgreSQL limits.

4. **Connection Multiplexing**: External poolers maintain a small pool of persistent database connections (e.g., 50-100) and multiplex hundreds or thousands of application connections onto them. This dramatically reduces database server load while allowing applications to maintain large pools.

### Architecture with External Pooling

```
┌─────────────────┐
│  Fides Worker 1 │──┐
│  (300 conns)    │  │
└─────────────────┘  │
                     │    ┌──────────────┐         ┌────────────────┐
┌─────────────────┐  ├───▶│  PgBouncer   │────────▶│   PostgreSQL   │
│  Fides Worker 2 │──┤    │  (50 conns)  │         │  (50 backends) │
│  (300 conns)    │  │    └──────────────┘         └────────────────┘
└─────────────────┘  │
                     │
┌─────────────────┐  │
│  Fides Worker 3 │──┘
│  (300 conns)    │
└─────────────────┘

Total app connections: 900
Total database backends: 50 (multiplexed)
```

### Configuration with External Pooling

When using an external connection pooler, you can safely configure larger application-side pools:

```bash
# Point to PgBouncer instead of directly to PostgreSQL
FIDES__DATABASE__SERVER=pgbouncer.internal.example.com
FIDES__DATABASE__PORT=6432

# Configure larger application pools (safe with external pooling)
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SIZE=300
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PREWARM=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SKIP_ROLLBACK=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_AUTOCOMMIT=true
```

**Important PgBouncer Configuration:**
- Use **transaction pooling mode** (not session mode) for best multiplexing
- With transaction pooling, ensure you set `pool_skip_rollback=true` in Fides (already recommended)
- Be aware that transaction pooling has limitations with certain PostgreSQL features (prepared statements, LISTEN/NOTIFY, etc.)

### When You Might Not Need External Pooling

External pooling may not be necessary if:
- You have a single Fides instance with modest traffic (<100 req/s)
- Your PostgreSQL server has abundant resources (high memory, low connection limit concerns)
- You're running a development/staging environment
- Total connections across all workers remain well under PostgreSQL's `max_connections` limit

However, for production deployments expecting high traffic, external pooling is considered a best practice and will significantly improve both application and database performance.

## Why These Optimizations Matter

### Connection Establishment Cost

Establishing new database connections is an expensive operation, especially under high load. Each new connection requires:
- TCP handshake
- SSL/TLS negotiation (if enabled)
- Database authentication
- Session initialization

Under heavy traffic, these costs compound and can lead to:
- Increased latency for user requests
- Database connection exhaustion
- Cascading failures under load spikes

**Pre-warming the connection pool** solves this by establishing all connections at startup, ensuring they're immediately available when requests arrive.

### Rollback Overhead

By default, SQLAlchemy performs a rollback operation when returning connections to the pool. For read-only queries, this rollback is unnecessary overhead that adds latency to every database operation.

**Skipping rollback on return** eliminates this unnecessary work for read-only operations, improving throughput and reducing latency.

## Configuration for higher-throughput scenarios

All configuration is done via environment variables with the `FIDES__DATABASE__` prefix.

### Required Configuration

First, ensure you have a read-only database replica configured:

```bash
# Read-only database server (required for all settings below)
FIDES__DATABASE__READONLY_SERVER=readonly-db.example.com
FIDES__DATABASE__READONLY_PORT=5432
FIDES__DATABASE__READONLY_USER=fides_readonly
FIDES__DATABASE__READONLY_PASSWORD=your_password
FIDES__DATABASE__READONLY_DB=fides
```

### Recommended Performance Settings

For optimal performance under load, configure these settings together:

```bash
# Enable connection pool pre-warming (RECOMMENDED)
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PREWARM=true

# Set pool size based on expected peak concurrent requests (start with 300)
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SIZE=300

# Disable rollback on connection return (RECOMMENDED for read-only)
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SKIP_ROLLBACK=true

# Enable autocommit for read-only operations (RECOMMENDED)
FIDES__DATABASE__ASYNC_READONLY_DATABASE_AUTOCOMMIT=true

# Allow overflow connections for traffic spikes
FIDES__DATABASE__ASYNC_READONLY_DATABASE_MAX_OVERFLOW=50

# Enable pre-ping to verify connection health
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PRE_PING=true
```

## Environment Variables Explained

### `FIDES__DATABASE__ASYNC_READONLY_DATABASE_PREWARM`

**Type:** Boolean  
**Default:** `false`  
**Recommended:** `true` for production

**What it does:**  
When enabled, Fides will establish all connections in the pool during application startup rather than lazily creating them on-demand.

**SQLAlchemy Reference:** While SQLAlchemy doesn't have built-in pre-warming, Fides implements this by checking out all connections and returning them to the pool. See [Pool.connect()](https://docs.sqlalchemy.org/en/14/core/pooling.html#sqlalchemy.pool.Pool.connect) for the underlying mechanism.

**Why it's important:**  
- Eliminates connection establishment latency for initial requests
- Provides predictable performance from the moment the application starts
- Prevents connection storms during traffic spikes
- Allows you to detect connection issues at startup rather than during request handling

**Trade-offs:**  
- Increases application startup time proportional to pool size
- Requires your database to handle all connections immediately
- All connections count against your database's max connection limit from startup

**When to use:**  
Enable this for production environments with predictable traffic patterns where consistent low latency is critical.

---

### `FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SIZE`

**Type:** Integer  
**Default:** `5`  
**Recommended:** Start with `300`, adjust based on performance testing

**What it does:**  
Sets the maximum number of concurrent database connections maintained in the pool. These connections are reused for multiple requests.

**SQLAlchemy Reference:** [pool_size parameter](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.pool_size) in create_engine() documentation. Note that SQLAlchemy pools start with zero connections and grow lazily to this size.

**Why it's important:**  
- Determines how many concurrent read-only database operations can execute simultaneously
- Must be sized to handle peak concurrent request volume
- Too small: requests queue waiting for available connections, increasing latency
- Too large: wastes database resources and may exceed database connection limits

**How to size it:**  
1. **Start with 300 connections** as a baseline for high-traffic applications
2. Monitor these metrics during load testing:
   - Connection pool utilization (should not regularly reach 100%)
   - Request latency (p95, p99 percentiles)
   - Database connection count
3. Adjust based on observations:
   - Increase if: Pool exhaustion occurs, high latency during peak traffic
   - Decrease if: Database connection limits approached, pool rarely exceeds 50% utilization

**Formula for estimation:**  
```
pool_size ≈ (peak_requests_per_second × average_query_duration_seconds) × 1.5
```

For example:
- 1000 req/s with 200ms average query time: `1000 × 0.2 × 1.5 = 300 connections`

**Important considerations:**  
- Each worker/pod needs its own pool, so total connections = `pool_size × number_of_workers`
- Your database must support total concurrent connections from all sources
- PostgreSQL default max_connections is typically 100-200 (often needs increasing)

---

### `FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SKIP_ROLLBACK`

**Type:** Boolean  
**Default:** `false`  
**Recommended:** `true` for read-only databases

**What it does:**  
When enabled, SQLAlchemy skips executing `ROLLBACK` when returning connections to the pool by setting `pool_reset_on_return=None`.

**SQLAlchemy Reference:** [Reset On Return](https://docs.sqlalchemy.org/en/14/core/pooling.html#reset-on-return) and [pool_reset_on_return parameter](https://docs.sqlalchemy.org/en/14/core/pooling.html#sqlalchemy.pool.Pool.params.reset_on_return) documentation.

**Why it's important:**  
- **Massive performance gain:** Eliminates unnecessary round-trip to database for every query
- Read-only queries never modify data, so rollback serves no purpose
- Under high load, this can reduce database CPU usage by 20-30%
- Reduces connection return latency, improving overall throughput

**Technical details:**  
By default, SQLAlchemy sets `pool_reset_on_return='rollback'` which executes:
```sql
ROLLBACK;  -- Unnecessary for read-only operations
```

With this setting enabled, connections are returned to the pool without any cleanup, trusting that read-only operations leave no state to clean up.

**Safety:**  
This is safe for read-only replicas because:
- Read-only queries cannot modify data
- No transaction state needs to be cleaned up
- Subsequent queries will start fresh transactions anyway

**When to use:**  
Always enable this for read-only database connections. Only disable if you're using the same connection pool for both read and write operations (not recommended).

---

### `FIDES__DATABASE__ASYNC_READONLY_DATABASE_AUTOCOMMIT`

**Type:** Boolean  
**Default:** `false`  
**Recommended:** `true` for read-only databases

**What it does:**  
Enables PostgreSQL autocommit mode by setting `isolation_level='AUTOCOMMIT'`.

**SQLAlchemy Reference:** [Setting Transaction Isolation Levels including DBAPI Autocommit](https://docs.sqlalchemy.org/en/14/core/connections.html#dbapi-autocommit) and [isolation_level parameter](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.isolation_level).

**Why it's important:**  
- Eliminates explicit `BEGIN` and `COMMIT` statements for read queries
- Reduces overhead for simple SELECT queries
- Prevents long-running read transactions from holding resources
- Works synergistically with `pool_skip_rollback` for maximum performance

**Technical details:**  
Without autocommit, PostgreSQL wraps queries in transactions:
```sql
BEGIN;
SELECT * FROM users WHERE id = 1;
COMMIT;
```

With autocommit enabled:
```sql
-- No BEGIN/COMMIT overhead
SELECT * FROM users WHERE id = 1;
```

**Trade-offs:**  
- Cannot use explicit transaction blocks in read-only queries
- May see slight inconsistencies if multiple queries in a request read data that changes between calls

**When to use:**  
Enable for read-only replicas where you don't need transaction isolation across multiple queries in a single request.

---

### `FIDES__DATABASE__ASYNC_READONLY_DATABASE_MAX_OVERFLOW`

**Type:** Integer  
**Default:** `10`  
**Recommended:** `50-100` for production

**What it does:**  
Allows the pool to create additional temporary connections beyond `pool_size` when all pool connections are in use. These overflow connections are closed (not pooled) after use.

**SQLAlchemy Reference:** [max_overflow parameter](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.max_overflow) in create_engine() documentation.

**Why it's important:**  
- Provides safety valve for unexpected traffic spikes
- Prevents request failures during brief bursts above normal capacity
- Overflow connections are temporary and released after use

**How to size it:**  
Set to 15-20% of your pool size to handle bursts without excessive resource consumption.

**Trade-offs:**  
- Overflow connections are not pre-warmed (must be established on-demand)
- Creating overflow connections is expensive (connection establishment cost)
- Too many overflow connections may exceed database limits

---

### `FIDES__DATABASE__ASYNC_READONLY_DATABASE_PRE_PING`

**Type:** Boolean  
**Default:** `true`  
**Recommended:** `true`

**What it does:**  
Before using a connection from the pool, SQLAlchemy executes a lightweight query to verify the connection is still valid.

**SQLAlchemy Reference:** [Disconnect Handling - Pessimistic](https://docs.sqlalchemy.org/en/14/core/pooling.html#disconnect-handling-pessimistic) and [pool_pre_ping parameter](https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.pool_pre_ping).

**Why it's important:**  
- Detects stale connections (closed by database, network issues, timeouts)
- Prevents query failures from dead connections
- Automatically establishes new connection if pre-ping fails

**Technical details:**  
Executes a simple query like `SELECT 1` before each connection use.

**Trade-offs:**  
- Adds minimal overhead (microseconds) per query
- Worth it to prevent errors from stale connections

**When to disable:**  
Only disable if you have very aggressive connection keepalives and can guarantee connections never go stale.

## Example Configurations

### High-Traffic Production (Recommended)

For applications with 500+ requests per second:

```bash
# Read-only replica configuration
FIDES__DATABASE__READONLY_SERVER=readonly.db.prod.internal
FIDES__DATABASE__READONLY_PORT=5432
FIDES__DATABASE__READONLY_USER=fides_readonly
FIDES__DATABASE__READONLY_PASSWORD=secure_password

# Optimized pool settings
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PREWARM=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SIZE=300
FIDES__DATABASE__ASYNC_READONLY_DATABASE_MAX_OVERFLOW=50
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SKIP_ROLLBACK=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_AUTOCOMMIT=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PRE_PING=true
```

### Medium-Traffic Production

For applications with 100-500 requests per second:

```bash
FIDES__DATABASE__READONLY_SERVER=readonly.db.prod.internal
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PREWARM=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SIZE=100
FIDES__DATABASE__ASYNC_READONLY_DATABASE_MAX_OVERFLOW=25
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SKIP_ROLLBACK=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_AUTOCOMMIT=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PRE_PING=true
```

### Development/Staging

Smaller pool for non-production environments:

```bash
FIDES__DATABASE__READONLY_SERVER=readonly.db.staging.internal
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PREWARM=false
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SIZE=10
FIDES__DATABASE__ASYNC_READONLY_DATABASE_MAX_OVERFLOW=5
FIDES__DATABASE__ASYNC_READONLY_DATABASE_POOL_SKIP_ROLLBACK=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_AUTOCOMMIT=true
FIDES__DATABASE__ASYNC_READONLY_DATABASE_PRE_PING=true
```

## Performance Testing & Tuning

### Metrics to Monitor

Monitor these metrics to validate your configuration:

1. **Connection Pool Utilization**
   - Should stay below 80% during normal operation
   - Brief spikes to 100% are acceptable during traffic bursts
   - Consistently at 100% means pool is undersized

2. **Request Latency**
   - Track p50, p95, p99 response times
   - Compare before/after optimization changes
   - Look for latency spikes during high load

3. **Database Connections**
   - Total active connections: `pool_size × number_of_workers`
   - Monitor database connection count doesn't exceed limits

4. **Database CPU/Memory**
   - Should decrease with `pool_skip_rollback` enabled
   - Monitor for resource exhaustion

### Load Testing Procedure

1. **Baseline:** Test with default settings (small pool, no optimizations)
2. **Enable skip_rollback:** Measure improvement (typically 20-40% latency reduction)
3. **Increase pool_size:** Increment by 50, test until latency stabilizes
4. **Enable prewarm:** Verify startup time acceptable, measure cold-start elimination
5. **Validate under burst traffic:** Test with traffic spikes to validate overflow settings

### Signs You Need to Adjust

**Increase pool_size if:**
- Frequent "TimeoutError: Connection pool exhausted" errors
- High p95/p99 latency during peak traffic
- Connection pool utilization consistently above 80%

**Decrease pool_size if:**
- Database connection limits are being approached
- Pool utilization rarely exceeds 30-40%
- Database resource costs are concern

**Disable prewarm if:**
- Application startup time is unacceptably long
- Connection issues during startup
- Running in environments with very short-lived containers

## Database Configuration Requirements

### PostgreSQL Configuration

Ensure your PostgreSQL database can handle the connection load:

```sql
-- Check current max_connections setting
SHOW max_connections;

-- Typical production setting for high-traffic deployments
-- File: postgresql.conf
max_connections = 1000

-- Monitor current connection usage
SELECT count(*) FROM pg_stat_activity;
```

**Sizing max_connections:**
```
max_connections ≥ (pool_size × number_of_fides_workers) + connections_for_other_services + 50
```

### Read Replica Configuration

For read-only replicas, ensure:

1. **Replication lag is acceptable** for your use case
2. **Hot standby is enabled** (PostgreSQL)
3. **User has appropriate read-only permissions**

```sql
-- Create read-only user
CREATE USER fides_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE fides TO fides_readonly;
GRANT USAGE ON SCHEMA public TO fides_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO fides_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO fides_readonly;
```

## Troubleshooting

### Connection Pool Exhaustion

**Symptoms:**  
```
asyncio.TimeoutError: Connection pool exhausted
```

**Solutions:**
- Increase `ASYNC_READONLY_DATABASE_POOL_SIZE`
- Increase `ASYNC_READONLY_DATABASE_MAX_OVERFLOW`
- Check for connection leaks (unclosed connections)
- Verify queries are not taking excessively long

### Slow Startup

**Symptoms:**  
Application takes minutes to start when prewarm is enabled.

**Solutions:**
- Reduce `ASYNC_READONLY_DATABASE_POOL_SIZE`
- Disable prewarm for development environments
- Check database connection latency/network issues
- Verify database can handle concurrent connection requests

### Database Connection Limit Exceeded

**Symptoms:**
```
FATAL: remaining connection slots are reserved
```

**Solutions:**
- Increase PostgreSQL `max_connections` setting
- Reduce pool_size across all workers
- Calculate total connections: `pool_size × workers + other_services`

### High Latency Despite Optimizations

**Potential causes:**
- Queries themselves are slow (check query performance)
- Database replica has high replication lag
- Network latency between Fides and database
- Database CPU/memory exhaustion
- Pool size still too small for traffic volume

## Best Practices

1. **Always enable skip_rollback for read-only pools** - Free performance win with no downsides
2. **Start with prewarm disabled**, enable once pool size is properly tuned
3. **Size pool based on actual load testing**, not guesswork
4. **Monitor pool utilization continuously** in production
5. **Plan for 2x capacity** to handle traffic spikes gracefully
6. **Configure database connection limits** before enabling large pools
7. **Use separate pools** for read-only and read-write operations (Fides does this by default)
8. **Test disaster recovery** - what happens when database is unreachable?

## Additional Resources

### SQLAlchemy Documentation (Version 1.4)
- [Connection Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html) - Complete pooling guide
- [Reset On Return](https://docs.sqlalchemy.org/en/14/core/pooling.html#reset-on-return) - Detailed explanation of reset behavior
- [Dealing with Disconnects](https://docs.sqlalchemy.org/en/14/core/pooling.html#dealing-with-disconnects) - Pessimistic and optimistic disconnect handling
- [Pool Events](https://docs.sqlalchemy.org/en/14/core/pooling.html#pool-events) - Hooks for pool lifecycle events
- [Engine Configuration](https://docs.sqlalchemy.org/en/14/core/engines.html) - All create_engine() parameters
- [Transaction Isolation Levels](https://docs.sqlalchemy.org/en/14/core/connections.html#setting-transaction-isolation-levels-dbapi-autocommit) - AUTOCOMMIT and other isolation levels
- [Asynchronous I/O Support](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html) - Async engine documentation

### Database-Specific Documentation
- [asyncpg Connection Pools](https://magicstack.github.io/asyncpg/current/usage.html#connection-pools) - asyncpg performance tuning
- [PostgreSQL Connection Management](https://www.postgresql.org/docs/current/runtime-config-connection.html) - PostgreSQL connection settings
- [PostgreSQL max_connections](https://www.postgresql.org/docs/current/runtime-config-connection.html#GUC-MAX-CONNECTIONS) - Configuring connection limits

### Related Fides Documentation
- Check `src/fides/config/database_settings.py` for all available database configuration options
- See `src/fides/api/db/ctl_session.py` for the async connection pool implementation

## Summary

For most production deployments expecting high traffic:

✅ **Always enable:** `pool_skip_rollback=true` and `autocommit=true`  
✅ **Start with:** `pool_size=300` and adjust based on load testing  
✅ **Enable in production:** `prewarm=true` after pool size is tuned  
✅ **Monitor:** Connection pool utilization, request latency, database connections  
✅ **Test thoroughly:** Validate configuration under realistic load before deploying  

These optimizations can reduce latency by 30-50% and significantly improve throughput under load.
