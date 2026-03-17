---- MODULE DsrWatchdog ----
(***********************************************************************)
(* TLA+ specification for the DSR watchdog / requeue logic in fides   *)
(*                                                                     *)
(* Source: src/fides/api/service/privacy_request/request_service.py   *)
(*         poll_for_exited_privacy_request_tasks (lines 630-725)       *)
(*                                                                     *)
(* Models the interaction between:                                     *)
(*   - ParentTask: the Celery task that dispatches subtasks; can die   *)
(*                 at any point between dispatches                     *)
(*   - SubTask workers: execute individual RequestTasks                *)
(*   - Watchdog: scheduled job that detects stuck/interrupted          *)
(*               privacy requests and decides to cancel or requeue     *)
(*                                                                     *)
(* TASK GRAPH (N=2 tasks, linear chain):                               *)
(*   Task 1 (root, no upstream) --> Task 2                             *)
(*   Upstream[1] = {}, Upstream[2] = {1}                              *)
(*                                                                     *)
(* BUG BEING MODELED:                                                  *)
(*   The watchdog has two related bugs:                                *)
(*   BUG 1 (ENG-2756 gap): a pending task with upstream complete       *)
(*     but no subtask_id is incorrectly cancelled. The ENG-2756 guard  *)
(*     only protected pending+awaiting_upstream=TRUE.                  *)
(*   BUG 2: in_processing+no_subtask_id is hard-cancelled, bypassing   *)
(*     the _handle_privacy_request_requeue retry mechanism entirely.   *)
(*                                                                     *)
(* DESIGN:                                                             *)
(*   ALL no-subtask_id cases (both pending and in_processing) should   *)
(*   go through _handle_privacy_request_requeue, which applies a       *)
(*   retry limit (privacy_request_requeue_retry_count config).         *)
(*   Cancellation only happens when the retry limit is exhausted.      *)
(*                                                                     *)
(* TWO WATCHDOG VARIANTS:                                              *)
(*   Spec      - Buggy watchdog (hard-cancels, bypasses retry).        *)
(*   SpecFixed - Corrected watchdog (retry logic, all invariants pass) *)
(*                                                                     *)
(* KEY CORRECTNESS INVARIANT:                                          *)
(*   CancelImpliesRetriesExhausted - pr_status = "error" is only       *)
(*     reachable when retry_count >= MaxRetries. Cancellation is never *)
(*     a first-resort response; it only happens after the configured   *)
(*     number of requeue attempts have all failed.                     *)
(*                                                                     *)
(* LIVENESS:                                                           *)
(*   EventualResolution: after the parent dies, the privacy request    *)
(*   eventually reaches a terminal state (error, requeued, complete).  *)
(*                                                                     *)
(* NOT MODELED:                                                        *)
(*   - Redis cache expiry / eviction (treated as subtask_cached=FALSE  *)
(*     at task creation; a separate CacheEvicted action models runtime *)
(*     eviction as an adversarial step)                                *)
(*   - requires_input branch (modeled as abstract skip)                *)
(*   - has_async_tasks_awaiting_external_completion branch (skip)      *)
(*   - Celery broker queue inspection (subtask_alive abstracts this)   *)
(*   - Re-execution after requeue (requeued is treated as terminal     *)
(*     for spec tractability; the invariant is about the cancel path)  *)
(***********************************************************************)

EXTENDS Integers, FiniteSets, TLC

\* ================================================================== *
\* STATE SPACE CONSTANTS                                              *
\* ================================================================== *

\* Set of task identifiers. Model with {1, 2}.
\* Task 1 is the root (no upstream). Task 2 depends on Task 1.
Tasks == {1, 2}

\* Upstream task sets. Maps each task to its set of prerequisite tasks.
\* Mirrors RequestTask.upstream_tasks (list of collection address strings).
\* Here simplified to task IDs for a linear 2-task chain.
Upstream == (1 :> {} @@ 2 :> {1})

\* Maximum number of requeue attempts before a privacy request is cancelled.
\* Mirrors: privacy_request_requeue_retry_count config option.
\* Set via .cfg: MaxRetries = 2
CONSTANT MaxRetries

\* ================================================================== *
\* TYPE DEFINITIONS                                                   *
\* ================================================================== *

\* Mirrors ExecutionLogStatus enum on RequestTask.status.
\* "skipped" is included because COMPLETED_EXECUTION_LOG_STATUSES = [complete, skipped].
TaskStatuses == {"pending", "in_processing", "complete", "skipped", "error", "cancelled"}

\* Mirrors PrivacyRequestStatus for the overall request outcome.
PrStatuses == {"running", "requeued", "error", "complete"}

\* Mirrors COMPLETED_EXECUTION_LOG_STATUSES in execution_log.py.
\* NOTE: "error" and "cancelled" are NOT in this set — a task that
\* errored does NOT unblock its downstream tasks.
CompletedStatuses == {"complete", "skipped"}

\* ================================================================== *
\* STATE VARIABLES                                                    *
\* ================================================================== *

VARIABLES
    task_status,    \* [Tasks -> TaskStatuses]
                    \* Mirrors RequestTask.status in the database.

    subtask_cached, \* [Tasks -> BOOLEAN]
                    \* TRUE if this task's Celery ID has been written to Redis.
                    \* Mirrors: cache.get(get_async_task_tracking_cache_key(task.id))

    subtask_alive,  \* [Tasks -> BOOLEAN]
                    \* TRUE if the subtask's Celery task is in the queue or running.
                    \* Abstracts: celery_tasks_in_flight([subtask_id]) in the watchdog.
                    \* Only meaningful when subtask_cached = TRUE.

    parent_alive,   \* BOOLEAN
                    \* TRUE while the parent Celery task (run_privacy_request) is alive.
                    \* Parent death models: OOM kill, pod restart, Celery worker crash.

    pr_status,      \* PrStatuses
                    \* Mirrors PrivacyRequest.status outcome after watchdog runs.

    retry_count     \* 0..MaxRetries
                    \* Number of times the privacy request has been requeued.
                    \* Mirrors: the retry counter checked by _handle_privacy_request_requeue
                    \*   against privacy_request_requeue_retry_count config.

vars == <<task_status, subtask_cached, subtask_alive, parent_alive, pr_status, retry_count>>

\* ================================================================== *
\* HELPERS                                                            *
\* ================================================================== *

\* True when all upstream tasks for t have reached a completed status.
\* Mirrors the awaiting_upstream computation in _get_request_task_ids_in_progress:
\*   awaiting_upstream = any(
\*     status_by_address.get((addr, task.action_type))
\*     not in COMPLETED_EXECUTION_LOG_STATUSES
\*     for addr in upstream_addrs
\*   )
\* Note: awaiting_upstream=TRUE means NOT all upstream are complete.
\*       UpstreamComplete=TRUE means all upstream ARE complete (inverse).
UpstreamComplete(t) ==
    \A u \in Upstream[t] : task_status[u] \in CompletedStatuses

\* ================================================================== *
\* INITIAL STATE                                                      *
\* ================================================================== *

Init ==
    /\ task_status    = [t \in Tasks |-> "pending"]
    /\ subtask_cached = [t \in Tasks |-> FALSE]
    /\ subtask_alive  = [t \in Tasks |-> FALSE]
    /\ parent_alive   = TRUE
    /\ pr_status      = "running"
    /\ retry_count    = 0

\* ================================================================== *
\* SYSTEM ACTIONS                                                     *
\* ================================================================== *

\* Parent dispatches a RequestTask to Celery and caches the task ID.
\* Sequence in execute_request_tasks.py:
\*   1. celery_task = celery_task_fn.apply_async(...)
\*   2. cache_task_tracking_key(request_task.id, celery_task.task_id)
\* Modeled as atomic (the window between apply_async and cache write
\* is not the failure mode we are investigating here).
DispatchTask(t) ==
    /\ parent_alive = TRUE
    /\ pr_status = "running"
    /\ task_status[t] = "pending"
    /\ UpstreamComplete(t)
    /\ ~subtask_cached[t]
    /\ subtask_cached' = [subtask_cached EXCEPT ![t] = TRUE]
    /\ subtask_alive'  = [subtask_alive  EXCEPT ![t] = TRUE]
    /\ UNCHANGED <<task_status, parent_alive, pr_status, retry_count>>

\* Celery worker picks up the dispatched task and starts executing it.
\* This transitions task_status from "pending" to "in_processing".
StartExecution(t) ==
    /\ task_status[t] = "pending"
    /\ subtask_cached[t] = TRUE
    /\ task_status' = [task_status EXCEPT ![t] = "in_processing"]
    /\ UNCHANGED <<subtask_cached, subtask_alive, parent_alive, pr_status, retry_count>>

\* Task completes successfully.
\* Guarded on pr_status = "running": once a privacy request has been
\* cancelled or requeued, its in-flight tasks are also considered
\* stopped. This reflects the real system: a cancelled PR's execution
\* logs are marked as errored and no further status changes are applied.
\* If all tasks are now complete, the privacy request is done.
CompleteTask(t) ==
    /\ task_status[t] = "in_processing"
    /\ pr_status = "running"
    /\ task_status'    = [task_status    EXCEPT ![t] = "complete"]
    /\ subtask_alive'  = [subtask_alive  EXCEPT ![t] = FALSE]
    /\ IF \A tt \in Tasks : task_status'[tt] \in CompletedStatuses
       THEN pr_status' = "complete"
       ELSE UNCHANGED pr_status
    /\ UNCHANGED <<subtask_cached, parent_alive, retry_count>>

\* Parent Celery task dies. Can happen between any two dispatches.
\* This is the failure mode that causes tasks to be left pending
\* without a subtask_id.
ParentDies ==
    /\ parent_alive = TRUE
    /\ parent_alive' = FALSE
    /\ UNCHANGED <<task_status, subtask_cached, subtask_alive, pr_status, retry_count>>

\* A cached subtask's Celery task stops running (exits the queue/worker).
\* Models: Celery worker crash, OOM kill, or task completion of parent.
\* This is the "subtask not in flight" case that triggers requeueing
\* in the watchdog's cached-task branch.
SubtaskExits(t) ==
    /\ subtask_cached[t] = TRUE
    /\ subtask_alive[t] = TRUE
    /\ subtask_alive' = [subtask_alive EXCEPT ![t] = FALSE]
    /\ UNCHANGED <<task_status, subtask_cached, parent_alive, pr_status, retry_count>>

\* Redis cache eviction: task ID is lost from cache while task may
\* still be running. Models the in_processing+no_subtask_id "stuck" case.
CacheEvicted(t) ==
    /\ subtask_cached[t] = TRUE
    /\ subtask_cached' = [subtask_cached EXCEPT ![t] = FALSE]
    /\ UNCHANGED <<task_status, subtask_alive, parent_alive, pr_status, retry_count>>

\* ================================================================== *
\* WATCHDOG — BUGGY LOGIC                                             *
\* Hard-cancels without going through the retry mechanism.           *
\*                                                                    *
\* BUG 1: pending+no_cache+upstream_complete → cancel directly        *
\*   (ENG-2756 guard only protected pending+awaiting_upstream=TRUE)   *
\* BUG 2: in_processing+no_cache → cancel directly                    *
\*   (bypasses _handle_privacy_request_requeue retry logic entirely)  *
\*                                                                    *
\* Both bugs violate CancelImpliesRetriesExhausted because retry_count *
\* is not consulted at all — the watchdog cancels on first encounter. *
\*                                                                    *
\*   for (request_task_id, task_status, awaiting_upstream)            *
\*       in request_tasks_in_progress:                                *
\*     subtask_id = get_cached_task_id(request_task_id)               *
\*     if not subtask_id:                                             *
\*       if task_status == pending and awaiting_upstream:              *
\*         continue   <-- ENG-2756 fix                                *
\*       # BUG 1: pending+NOT awaiting_upstream falls through here    *
\*       # BUG 2: in_processing also falls through here               *
\*       cancel_privacy_request()    <-- bypasses retry logic         *
\*       break                                                        *
\*     elif subtask_id not in queue and not in_flight:                *
\*       should_requeue = True                                        *
\*       break                                                        *
\* ================================================================== *

\* Computes the watchdog's decision given the current state.
\* "cancel"  -> pr_status := "error"
\* "requeue" -> pr_status := "requeued"
\* "skip"    -> no change (watchdog finds nothing actionable)
WatchdogDecisionBuggy ==
    LET in_progress == {t \in Tasks :
            task_status[t] \in {"pending", "in_processing"}}
    IN
    \* First task that triggers a decision (order matters in the real loop,
    \* but for safety invariants we check the worst-case: any such task).
    IF \E t \in in_progress :
        \* Task has no subtask_id AND is not protected by ENG-2756 guard.
        \* ENG-2756 guard: pending AND awaiting_upstream (= NOT UpstreamComplete).
        \* Buggy fall-through: pending+NOT awaiting_upstream, or in_processing+no_cache.
        /\ ~subtask_cached[t]
        /\ ~(task_status[t] = "pending" /\ ~UpstreamComplete(t))
    THEN "cancel"
    ELSE IF \E t \in in_progress :
        \* Has subtask_id but subtask is not running → requeue.
        /\ subtask_cached[t]
        /\ ~subtask_alive[t]
    THEN "requeue"
    ELSE "skip"

WatchdogRunBuggy ==
    /\ parent_alive = FALSE
    /\ pr_status = "running"
    /\ LET decision == WatchdogDecisionBuggy
       IN CASE decision = "cancel"  -> pr_status' = "error"
            [] decision = "requeue" -> pr_status' = "requeued"
            [] OTHER                -> UNCHANGED pr_status
    /\ UNCHANGED <<task_status, subtask_cached, subtask_alive, parent_alive, retry_count>>

\* ================================================================== *
\* WATCHDOG — FIXED LOGIC                                             *
\* ALL no-subtask_id cases route through the retry mechanism.        *
\*                                                                    *
\* Both pending and in_processing tasks with no subtask_id → requeue. *
\* _handle_privacy_request_requeue applies the retry limit:          *
\*   - retry_count < MaxRetries: requeue (pr_status := "requeued")   *
\*   - retry_count >= MaxRetries: cancel (pr_status := "error")      *
\*                                                                    *
\* Fixed code:                                                        *
\*   if not subtask_id:                                               *
\*     if task_status == requires_input: skip                         *
\*     if task_status == pending and awaiting_upstream: continue      *
\*     if has_async_tasks: skip                                       *
\*     # ALL other cases (pending+upstream_complete AND in_processing) *
\*     should_requeue = True                                          *
\*     break                                                          *
\*   # Then _handle_privacy_request_requeue applies retry logic       *
\* ================================================================== *

WatchdogDecisionFixed ==
    LET in_progress == {t \in Tasks :
            task_status[t] \in {"pending", "in_processing"}}
    IN
    \* ALL tasks with no subtask_id that aren't protected by the skip guards
    \* (requires_input, pending+awaiting_upstream, has_async_tasks) → requeue.
    \* Also: tasks with subtask_id but not running → requeue.
    \* The buggy distinction between pending and in_processing is gone.
    IF \E t \in in_progress :
        \/ \* No subtask_id and not waiting for upstream (actionable).
           \* Covers both:
           \*   pending+upstream_complete (parent died before dispatch)
           \*   in_processing+no_cache (cache evicted / parent died mid-write)
           (/\ ~subtask_cached[t]
            /\ ~(task_status[t] = "pending" /\ ~UpstreamComplete(t)))
        \/ \* Has subtask_id but subtask is not running.
           (/\ subtask_cached[t]
            /\ ~subtask_alive[t])
    THEN "requeue"
    ELSE "skip"

\* Applies the retry mechanism: requeue up to MaxRetries times, then cancel.
\* Mirrors _handle_privacy_request_requeue in request_service.py.
WatchdogRunFixed ==
    /\ parent_alive = FALSE
    /\ pr_status = "running"
    /\ LET decision == WatchdogDecisionFixed
       IN IF decision = "requeue"
          THEN IF retry_count < MaxRetries
               THEN \* Under the limit: requeue and increment counter.
                    /\ pr_status' = "requeued"
                    /\ retry_count' = retry_count + 1
               ELSE \* Retry limit exhausted: cancel.
                    /\ pr_status' = "error"
                    /\ UNCHANGED retry_count
          ELSE \* "skip": nothing actionable found.
               /\ UNCHANGED <<pr_status, retry_count>>
    /\ UNCHANGED <<task_status, subtask_cached, subtask_alive, parent_alive>>

\* ================================================================== *
\* NEXT-STATE RELATIONS                                               *
\* ================================================================== *

Next ==
    \/ \E t \in Tasks : DispatchTask(t)
    \/ \E t \in Tasks : StartExecution(t)
    \/ \E t \in Tasks : CompleteTask(t)
    \/ ParentDies
    \/ \E t \in Tasks : SubtaskExits(t)
    \/ \E t \in Tasks : CacheEvicted(t)
    \/ WatchdogRunBuggy

NextFixed ==
    \/ \E t \in Tasks : DispatchTask(t)
    \/ \E t \in Tasks : StartExecution(t)
    \/ \E t \in Tasks : CompleteTask(t)
    \/ ParentDies
    \/ \E t \in Tasks : SubtaskExits(t)
    \/ \E t \in Tasks : CacheEvicted(t)
    \/ WatchdogRunFixed

Spec      == Init /\ [][Next]_vars
SpecFixed == Init /\ [][NextFixed]_vars

\* ================================================================== *
\* FAIRNESS                                                           *
\* ================================================================== *

\* Weak fairness: if an action is continuously enabled, it eventually fires.
\* DispatchTask and CompleteTask need WF to ensure tasks make progress.
\* WF on Watchdog ensures it eventually fires when parent is dead.
Fairness ==
    /\ \A t \in Tasks : WF_vars(DispatchTask(t))
    /\ \A t \in Tasks : WF_vars(StartExecution(t))
    /\ \A t \in Tasks : WF_vars(CompleteTask(t))
    /\ WF_vars(WatchdogRunBuggy)

FairnessFixed ==
    /\ \A t \in Tasks : WF_vars(DispatchTask(t))
    /\ \A t \in Tasks : WF_vars(StartExecution(t))
    /\ \A t \in Tasks : WF_vars(CompleteTask(t))
    /\ WF_vars(WatchdogRunFixed)

FairSpec      == Spec      /\ Fairness
FairSpecFixed == SpecFixed /\ FairnessFixed

\* ================================================================== *
\* TYPE INVARIANT                                                     *
\* ================================================================== *

TypeOK ==
    /\ task_status    \in [Tasks -> TaskStatuses]
    /\ subtask_cached \in [Tasks -> BOOLEAN]
    /\ subtask_alive  \in [Tasks -> BOOLEAN]
    /\ parent_alive   \in BOOLEAN
    /\ pr_status      \in PrStatuses
    /\ retry_count    \in 0..MaxRetries

\* ================================================================== *
\* SAFETY INVARIANTS                                                  *
\* ================================================================== *

\* Primary safety invariant: cancellation is only a last resort.
\*
\* pr_status = "error" (cancellation) may only be reached after
\* retry_count has reached MaxRetries. The watchdog never cancels
\* on first encounter — it always attempts to requeue first and
\* only cancels once the configured retry limit is exhausted.
\*
\* This is the formal statement of: "_handle_privacy_request_requeue
\* is the single code path that cancels, and it only does so when
\* privacy_request_requeue_retry_count is exceeded."
\*
\* VIOLATED under Spec (buggy):
\*   WatchdogRunBuggy hard-cancels (pr_status := "error") without
\*   consulting retry_count. Minimal counterexample (3 states):
\*     1. Init: both tasks pending, retry_count=0
\*     2. ParentDies: parent dead
\*     3. WatchdogRunBuggy: pr_status -> "error", retry_count=0
\*   Fails because retry_count=0 < MaxRetries=2 but pr_status="error".
\*
\* PASSES under SpecFixed:
\*   WatchdogRunFixed only sets pr_status="error" in the ELSE branch
\*   of "retry_count < MaxRetries", so retry_count >= MaxRetries
\*   is guaranteed whenever pr_status = "error".
CancelImpliesRetriesExhausted ==
    pr_status = "error" => retry_count >= MaxRetries

\* ================================================================== *
\* LIVENESS                                                           *
\* ================================================================== *

TerminalPrStatuses == {"requeued", "error", "complete"}

\* After the parent task dies, the privacy request eventually reaches
\* a terminal state. Under the buggy spec this holds (it terminates
\* via incorrect cancellation). Under the fixed spec it also holds,
\* but via requeue (or genuine retry-exhausted error) instead.
EventualResolution ==
    (~parent_alive) ~> (pr_status \in TerminalPrStatuses)

====
