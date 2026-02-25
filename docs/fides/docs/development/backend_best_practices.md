# Backend Best Practices

This document outlines general best practices for backend development in Fides.

For database session management specifically, see `src/fides/api/db/SESSION_MANAGEMENT.md` in the source tree.

## Best Practices Summary

| Best Practice | Overview | When to Use |
|--------------|----------|-------------|
| [Use Celery worker tasks](#use-celery-worker-tasks-when-applicable) | Leverage async processing for scalability | Long-running tasks that need compute scalability |
| [Treat worker tasks as ephemeral](#treat-worker-tasks-as-ephemeral) | Design tasks to be killable and resumable | All worker tasks, especially long-running ones |
| [Don't over-rely on application memory](#do-not-over-rely-on-storing-state-in-application-memory) | Store persistent state in DB or Redis | State needed across API calls or between replicas |
| [Use read-only replicas](#use-read-only-replicas-for-database-and-cache) | Offload read queries to replica instances | Read-heavy operations that don't require write consistency |

---

## Use Celery Worker Tasks When Applicable

We deploy the main Fides webserver with a cluster of Celery worker nodes, which can and should be leveraged for asynchronous processing that requires scalability.

### When to Use

- When you require long-running, asynchronous tasks that can/should be decoupled from the webserver
- When those tasks require (or could eventually require) compute scalability

### How to Use

1. **Use the `celery_app.task` decorator** on your (non-async) function with the `DatabaseTask` base class:

```python
from fides.api.tasks import DatabaseTask, celery_app

@celery_app.task(base=DatabaseTask, bind=True)
def my_background_task(
    self: DatabaseTask,
    task_data: str,
):
    """Process data in the background."""
    with self.get_new_session() as session:
        # Your task logic here
        pass
```

2. **Set up a queue for your tasks** by defining a queue name constant and registering it in the `all_queues` list for the worker process. Queue names are defined in `fides.api.tasks`:

```python
MY_TASK_QUEUE_NAME = "fides.my_task_queue"
```

3. **Execute your task** by calling `apply_async` with the queue name:

```python
my_background_task.apply_async(
    queue=MY_TASK_QUEUE_NAME,
    kwargs={"task_data": "some_data"}
)
```

### Gotchas

- **Celery doesn't play nicely with async functions** — it inherently executes a synchronous function asynchronously with respect to the main webserver process. Define your tasks as regular (non-async) functions.
- **Coordinate with DevOps** — speak with the DevOps team about getting worker nodes deployed specifically for execution of your task(s).

---

## Treat Worker Tasks as Ephemeral

Worker tasks should be designed to run on infrastructure that may be terminated at any time. Think of worker compute as "cattle, not pets" — ephemeral resources that can come and go.

### Why This Matters

Our infrastructure uses autoscaling (HPA and KEDA) to dynamically adjust worker capacity based on demand. This enables:

- **Cost savings** — scale down idle workers, use cheaper spot instances
- **Better resiliency** — gracefully handle infrastructure failures
- **Easier deployments** — roll out updates without worrying about in-flight work
- **Elastic scaling** — automatically handle load spikes

However, autoscaling means worker pods can be terminated at any time:

- When Kubernetes scales inward, it sends a `SIGTERM` to pods and gives them a grace period to shut down
- Celery stops pulling new jobs during this period but must wrap up existing work
- Pods are selected for termination somewhat randomly — there's no guarantee a "busy" pod won't be killed
- Cloud providers may also reclaim spot instances with little warning

### Design Principles

**1. Make tasks killable and resumable**

Tasks should be able to be terminated at any point and resume from where they left off. Record progress checkpoints to persistent storage (database or Redis) so work isn't lost.

❌ **Bad**: Task that loses all progress if killed

```python
@celery_app.task(base=DatabaseTask, bind=True)
def process_all_items(self: DatabaseTask, item_ids: List[str]):
    results = []
    for item_id in item_ids:
        # If killed here, all progress is lost
        result = expensive_operation(item_id)
        results.append(result)

    # Only saves at the very end
    save_results(results)
```

✅ **Good**: Task that checkpoints progress and can resume

```python
@celery_app.task(base=DatabaseTask, bind=True)
def process_all_items(self: DatabaseTask, batch_id: str):
    with self.get_new_session() as session:
        batch = get_batch(session, batch_id)

        for item in batch.pending_items:
            result = expensive_operation(item.id)

            # Checkpoint after each item - progress is saved
            item.status = "completed"
            item.result = result
            session.commit()

    # Task can be re-invoked and will skip already-completed items
```

**2. Keep individual tasks small**

Break large jobs into smaller, independently-resumable units of work. This minimizes wasted work when a task is killed.

```python
# Instead of one massive task...
@celery_app.task
def process_entire_dataset(dataset_id: str):
    items = get_all_items(dataset_id)  # Could be thousands
    for item in items:
        process(item)  # Hours of work that could be lost

# ...use a coordinator that spawns small tasks
@celery_app.task
def process_dataset_coordinator(dataset_id: str):
    item_ids = get_item_ids(dataset_id)
    for item_id in item_ids:
        process_single_item.apply_async(kwargs={"item_id": item_id})

@celery_app.task
def process_single_item(item_id: str):
    # Small, quick task - minimal waste if killed
    process(item_id)
```

**3. Store task state externally**

Never rely on in-memory state to track task progress. Use the database or Redis to persist:

- Which items have been processed
- Current progress through a batch
- Intermediate results
- Error states and retry counts

### Gotchas

- **Some tasks can't easily be made resumable** — for example, tasks that interact with external systems in non-idempotent ways. For these, consider scheduling during low-traffic periods or setting minimum worker counts to reduce termination likelihood.
- **Database contention** — checkpointing frequently means more database writes. Balance checkpoint frequency against database load.
- **Idempotency matters** — if a task might be retried, ensure re-running it produces the same result (or gracefully handles already-completed work).

### Future Considerations

For complex, stateful workflows, consider dedicated workflow orchestration frameworks (e.g., Temporal) that provide built-in support for:

- Durable execution with automatic state persistence
- Workflow resumption after failures
- Activity retries with configurable policies
- Workflow versioning for safe deployments

---

## Do Not Over-Rely on Storing State in Application Memory

We often deploy Fides webservers as replicas behind a load balancer. Application memory is localized per instance, which means state can be inconsistent or lost between replicas.

### Guidelines

- **Application memory** should only be used to store local state needed within a particular task, e.g., within execution of an individual API function
- **Any state that needs persistence** across multiple API calls or for longer-running processes should instead be stored in the application database or Redis cache
- **Think longer-term** — sometimes state that is initially only needed locally eventually needs to be available more widely

### Examples

❌ **Bad**: Storing user session data in a module-level dictionary

```python
# This will cause issues with multiple webserver replicas!
_user_sessions: Dict[str, UserSession] = {}

@router.post("/session")
def create_session(user_id: str):
    _user_sessions[user_id] = UserSession(...)  # Lost on next request to different replica
```

✅ **Good**: Use Redis or database for shared state

```python
from fides.api.common_api.v1.endpoints.utils import get_cache

@router.post("/session")
def create_session(user_id: str):
    cache = get_cache()
    cache.set(f"session:{user_id}", session_data)  # Available to all replicas
```

---

## Use Read-Only Replicas for Database and Cache

Fides supports configuring both a writer and reader Redis, and a writer and reader database (PostgreSQL). We can take advantage of this to access the reader instances when not writing, improving performance and reducing load on the primary instances.

### When to Use

- When you only need to read data, and not write it
- Especially if the code you're writing needs to be performant
- For read-heavy operations that can tolerate minimal replication lag

### When NOT to Use

- If you're writing to storage
- If your read query immediately follows a write and requires the latest data
- If eventual consistency would cause issues for your use case

### How to Use

**For Redis**, use `get_read_only_cache` instead of `get_cache`:

```python
from fides.api.common_api.v1.endpoints.utils import get_read_only_cache

def get_cached_config():
    cache = get_read_only_cache()
    return cache.get("config_key")
```

**For PostgreSQL**, use `get_readonly_db` instead of `get_db`:

```python
from fides.api.api.deps import get_readonly_db

@router.get("/reports")
def get_reports(db: Session = Depends(get_readonly_db)):
    # Read-only queries go to the replica
    return db.query(Report).all()
```

### Gotchas

- **Replication lag** — In most cases, the delay between the writer and the reader replica should be negligible, but it's technically something that could come up. Don't use read replicas immediately after writes if you need to read your own writes.
