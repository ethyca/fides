# RequestTask Graph Invalidation on Reprocess

## Problem Statement

When a privacy request is reprocessed via Temporal, the traversal graph is rebuilt fresh from current dataset/connection configs. Existing `RequestTask` rows from the prior run hold real data: `access_data` retrieved from connectors, `data_for_erasures` prepared for masking, `rows_masked` from completed erasures, and `consent_sent` flags. We need a diffing + cascading invalidation system that determines which tasks can be preserved and which must be re-executed.

The Celery path sidesteps this: it reuses old `RequestTask` rows as-is, never rebuilds the graph, and just re-queues errored/pending tasks. That's the bug Temporal is solving.

---

## What Lives on a RequestTask

| Column | Written During | Content | Deletable? |
|--------|---------------|---------|------------|
| `access_data` | Access phase | Raw data retrieved from connector | Yes (re-fetchable) |
| `data_for_erasures` | Access phase | Access data with array placeholders preserved | Yes (derived from access_data) |
| `rows_masked` | Erasure phase | Count of rows erased/masked | **No** (irreversible) |
| `consent_sent` | Consent phase | Whether consent signal was sent | **No** (irreversible) |
| `callback_succeeded` | Callback async | Whether external callback completed | Depends on phase |
| `upstream_tasks` | Task creation | Immediate predecessor addresses | Stale on graph change |
| `downstream_tasks` | Task creation | Immediate successor addresses | Stale on graph change |
| `all_descendant_tasks` | Task creation | Transitive closure of descendants | Stale on graph change |
| `collection` | Task creation | Serialized Collection object | Stale on field/ref change |
| `traversal_details` | Task creation | Edges, input_keys, connection_key | Stale on graph change |

**Key insight**: `access_data` is re-fetchable. `rows_masked` and `consent_sent` are irreversible side effects. The invalidation system must distinguish between these.

---

## What Can Change Between Runs

### Category 1: Graph Topology Changes (affect which nodes exist and how they connect)

#### 1A. Connection disabled/enabled
- **Source**: `ConnectionConfig.disabled` field
- **Effect**: All collections for that connection appear/disappear from graph
- **Disabled**: Node removed. Downstream nodes lose an upstream dependency (may get different/fewer inputs). If node had completed access, data is orphaned but harmless.
- **Re-enabled**: Node appears. Downstream nodes gain a new upstream dependency. Need to execute this node and potentially re-execute downstream nodes that now have additional input data.
- **Applies to**: All task types (regular, manual, polling, callback)

#### 1B. Connection deleted
- **Source**: `ConnectionConfig` row deleted from DB
- **Effect**: Same as disabled. `GraphTask.__init__` sets `self.connector = None`, `skip_if_disabled()` raises `CollectionDisabled`.
- **Applies to**: All task types

#### 1C. Collection added to dataset
- **Source**: New collection in `DatasetConfig.ctl_dataset` JSON
- **Effect**: New node in graph. If it has references to/from existing collections, it creates new edges.
- **Applies to**: All task types (type determined by connection's manual/async config)

#### 1D. Collection removed from dataset
- **Source**: Collection removed from `DatasetConfig.ctl_dataset` JSON
- **Effect**: Node disappears. Downstream nodes lose upstream data. Existing `RequestTask` becomes orphan.
- **Applies to**: All task types

#### 1E. `skip_processing` toggled on collection
- **Source**: `collection.fides_meta.skip_processing`
- **Effect**: Same as add/remove. Collection excluded from graph when `skip_processing=True`.
- **Applies to**: All task types

#### 1F. Dataset added (new connection + dataset)
- **Source**: New `ConnectionConfig` + `DatasetConfig` created
- **Effect**: New nodes appear. May have references to existing collections.
- **Applies to**: All task types

#### 1G. Dataset removed (connection + dataset deleted)
- **Source**: `ConnectionConfig` + `DatasetConfig` deleted
- **Effect**: All nodes from that dataset disappear.
- **Applies to**: All task types

### Category 2: Edge Changes (affect data flow between nodes)

#### 2A. Field reference added
- **Source**: `field.fides_meta.references` gains a new entry
- **Effect**: New edge in graph. Target node now receives additional input from source node. Target node's query changes (more filter values). This can change what data gets retrieved.
- **Downstream cascade**: All descendants of the target node may receive different data.
- **Applies to**: Regular and manual tasks (async tasks don't use upstream data flow)

#### 2B. Field reference removed
- **Source**: `field.fides_meta.references` loses an entry
- **Effect**: Edge removed. Target node loses an input source. Query changes (fewer filter values). Different data retrieved.
- **Downstream cascade**: Same as 2A.
- **Applies to**: Regular and manual tasks

#### 2C. Field reference direction changed
- **Source**: `field.fides_meta.references[].direction` changed (from/to/bidirectional)
- **Effect**: Edge direction flips. Changes which node provides data to which.
- **Applies to**: Regular tasks

#### 2D. Identity field added/removed
- **Source**: `field.fides_meta.identity` added or removed
- **Effect**: Changes which collections are seed nodes (can start traversal with just identity data). May make previously unreachable collections reachable or vice versa.
- **Applies to**: All task types

#### 2E. `after` dependency added/removed (access)
- **Source**: `collection.fides_meta.after`
- **Effect**: Changes execution ordering. Collection must wait for specified predecessors. This is an ordering constraint, not a data dependency, but it changes the DAG shape.
- **Applies to**: Regular tasks during access phase

#### 2F. `erase_after` dependency added/removed
- **Source**: `collection.fides_meta.erase_after`
- **Effect**: Changes erasure execution ordering only. Erasure graph is flat (all nodes can run in parallel) except for `erase_after` constraints.
- **Applies to**: Regular tasks during erasure phase

### Category 3: Field Changes (affect what data is fetched/masked per node)

#### 3A. Field added to collection
- **Source**: New field in collection definition
- **Effect**: Connector retrieves additional data. `access_data` for this node would be different.
- **Downstream impact**: If the new field is referenced by downstream nodes, those nodes get new input.
- **Applies to**: Regular, manual (if field is in manual task definition), polling, callback

#### 3B. Field removed from collection
- **Source**: Field removed from collection definition
- **Effect**: Connector no longer retrieves that field. `access_data` changes.
- **Downstream impact**: If removed field was referenced by downstream nodes, those lose input.
- **Applies to**: Regular, manual, polling, callback

#### 3C. Field data_categories changed
- **Source**: `field.data_categories` modified
- **Effect**: Changes which fields match policy rules. Different fields get included in access results or targeted for erasure.
- **Downstream impact**: None (data categories affect filtering, not data flow)
- **Applies to**: All task types

#### 3D. Field masking_strategy_override changed
- **Source**: `field.fides_meta.masking_strategy_override` or `collection.fides_meta.masking_strategy_override`
- **Effect**: Different masking applied during erasure. If erasure already completed with old strategy, re-masking with new strategy may be needed.
- **Applies to**: Regular, polling, callback during erasure

#### 3E. Field return_all_elements changed
- **Source**: `field.fides_meta.return_all_elements`
- **Effect**: For array fields, changes whether all elements or only matching elements are returned. Changes `access_data` content.
- **Applies to**: Regular tasks

#### 3F. Field read_only toggled
- **Source**: `field.fides_meta.read_only`
- **Effect**: Read-only fields are not masked during erasure.
- **Applies to**: Regular tasks during erasure

### Category 4: Connection Config Changes (affect execution, not graph shape)

#### 4A. Secrets changed
- **Source**: `ConnectionConfig.secrets`
- **Effect**: Different credentials used. Same query, potentially different auth. May succeed where it failed before (or vice versa).
- **Applies to**: All task types

#### 4B. `enabled_actions` changed
- **Source**: `ConnectionConfig.enabled_actions`
- **Effect**: Erasure or consent action can be disabled per-connection. If erasure disabled, erasure task gets skipped (`ActionDisabled` exception). Access is never disabled.
- **Applies to**: Erasure and consent tasks only

#### 4C. `access` level changed (read vs write)
- **Source**: `ConnectionConfig.access` (AccessLevel enum)
- **Effect**: Write access required for erasure. If downgraded to read-only, erasure tasks fail.
- **Applies to**: Erasure tasks

#### 4D. SaaS config changed
- **Source**: `ConnectionConfig.saas_config` JSON
- **Effect**: Endpoint definitions, parameters, pagination, auth methods all change. Connector may retrieve different data or fail differently.
- **Applies to**: All task types for SaaS connectors

### Category 5: Policy Changes (affect what's included in results)

#### 5A. Policy rule targets changed
- **Source**: `Rule.targets` (data categories to include/exclude)
- **Effect**: Different fields included in access results package. Does not affect what data is retrieved from connectors. Affects the filtered output, not the raw `access_data`.
- **Applies to**: Access result filtering, not individual task execution

#### 5B. Rule masking_strategy changed
- **Source**: `Rule.masking_strategy`
- **Effect**: Different masking applied during erasure. Same risk as 3D.
- **Applies to**: Erasure tasks

### Category 6: Property-Based Filtering

#### 6A. Dataset property_ids changed
- **Source**: `DatasetConfig.property_ids`
- **Effect**: Dataset may be included/excluded from graph based on `privacy_request.property_id`
- **Applies to**: All task types

#### 6B. Collection property_scope changed
- **Source**: `collection.fides_meta.property_scope` (IN_SCOPE vs TRAVERSAL_ONLY)
- **Effect**: TRAVERSAL_ONLY collections provide FK data for downstream but skip access report and erasure. Switching to IN_SCOPE means the node now contributes to results.
- **Applies to**: Regular tasks

---

## Task-Type Specific Invalidation Considerations

### Regular Collection Tasks

Standard invalidation rules apply. The node runs `GraphTask.access_request()` / `erasure_request()` / `consent_request()`, each of which reads upstream data and writes results.

**Invalidation triggers**: All categories above.

**Re-execution safety**:
- Access: Safe to re-execute. Retrieves data again, overwrites `access_data`.
- Erasure: **Not idempotent** in general. Masking the same rows twice may not be harmful (applying NULL/hash again), but `rows_masked` count would be wrong. Connector-specific behavior varies.
- Consent: Sending consent signal twice is typically idempotent but depends on connector.

### Manual Tasks (ManualTaskGraphTask)

Manual tasks pause execution and wait for user-provided data via `ManualTaskInstance` submissions.

**Special invalidation concerns**:

1. **User-submitted data**: When a manual task completes, its `access_data` contains data the user provided, not data fetched from a connector. Re-executing means the user must re-submit. This is expensive (human in the loop).

2. **ManualTaskInstance lifecycle**: Manual task instances are created during graph construction (`privacy_request.create_manual_task_instances()`). If the manual connection's field definitions change, existing instances may not match.

3. **Conditional dependencies**: Manual tasks can have conditions (`_evaluate_conditions()`) that depend on privacy request fields or upstream data. If upstream data changes, conditions may evaluate differently.

**Invalidation triggers**:
- Categories 1, 2 apply (graph shape)
- Category 3 applies differently: field changes on manual collections mean the manual task definition changed, requiring new ManualTaskInstance creation
- Category 4A (secrets) is irrelevant (no connector auth)
- If upstream data to a manual task changes, the manual task itself does NOT need re-execution (it doesn't use upstream data for retrieval). But its access_data feeds downstream, so downstream may need re-execution.

**Re-execution cost**: High. Requires human action. Should be avoided unless the manual task definition itself changed.

### Async Polling Tasks

Polling tasks send an initial request, then poll for results. State is maintained across polls via `RequestTaskSubRequest` objects.

**Special invalidation concerns**:

1. **Sub-request state**: `RequestTaskSubRequest` rows track individual polling operations with their own `status`, `access_data`, `rows_masked`, and `param_values` (correlation IDs).

2. **In-flight operations**: If a polling task is mid-poll (status=`polling`), the external system is actively processing. Re-execution would mean:
   - Sending a duplicate initial request to the external system
   - Potentially creating duplicate processing on the remote side
   - Losing correlation to the in-flight operation

3. **Completion aggregation**: Polling completion is determined by all sub-requests reaching terminal status. Partial completion state would be lost on re-execution.

**Invalidation triggers**:
- Categories 1, 2 apply (graph shape)
- Category 3 applies: field changes affect what data is requested
- Category 4D (SaaS config) is critical: polling endpoint/param changes affect the request
- If upstream data changes, the polling request needs different input, requiring full re-execution

**Re-execution safety**:
- Access: Risky if external system doesn't handle duplicate requests idempotently
- Erasure: Same risks as regular erasure plus external system side effects
- Must check sub-request terminal status before deciding to re-execute

### Async Callback Tasks

Callback tasks send an initial request and wait for an external system to POST back with results.

**Special invalidation concerns**:

1. **Signal-based completion**: The workflow waits for a Temporal signal. If we invalidate and re-execute, we need to handle the case where the original callback arrives after we've already started a new execution.

2. **External system state**: The external system has been told to process a request. If we send a new one, we may get two callbacks. The workflow signal handler must be idempotent.

3. **No sub-requests**: Unlike polling, callback tasks don't track intermediate state. They either have `access_data`/`rows_masked` (complete) or don't (waiting).

**Invalidation triggers**:
- Same as polling tasks
- Category 4D is critical: callback endpoint changes mean the external system may call back to a different URL

**Re-execution safety**:
- Access: Risky (duplicate external processing)
- Erasure: Same risks as polling
- Must ensure old callbacks are discarded or handled gracefully

---

## Invalidation Algorithm

### Phase 1: Build Fresh Graph

```
1. Query all DatasetConfigs + ConnectionConfigs
2. Filter disabled connections
3. Apply property-based filtering
4. Build DatasetGraph via Traversal
5. Result: Set of nodes (collection addresses) + edges (field references)
```

### Phase 2: Build Old Graph from RequestTasks

```
1. Query existing RequestTasks for this privacy request + action type
2. For each task, extract:
   - collection_address → node identity
   - traversal_details.incoming_edges → edge set
   - traversal_details.outgoing_edges → edge set
   - traversal_details.input_keys → ordered upstream dependencies
   - collection (serialized) → field set, references, after deps
3. Result: Set of old nodes + old edges
```

### Phase 3: Diff

Compare old graph vs new graph across these dimensions:

```
A. Node diff:
   - ADDED nodes: in new graph but not in old RequestTasks
   - REMOVED nodes: in old RequestTasks but not in new graph
   - RETAINED nodes: in both

B. Edge diff (for RETAINED nodes):
   - For each retained node, compare:
     - incoming_edges (old traversal_details vs new traversal)
     - outgoing_edges (old traversal_details vs new traversal)
   - CHANGED: any edge added, removed, or direction changed

C. Field diff (for RETAINED nodes):
   - Compare serialized Collection from old RequestTask vs new Collection
   - Diff field set: added fields, removed fields
   - Diff field properties: data_categories, references, masking_strategy_override,
     return_all_elements, read_only, identity
   - CHANGED: any field difference

D. Connection config diff (for RETAINED nodes):
   - Compare connection_key from old traversal_details vs new
   - Check if connection's enabled_actions changed
   - Check if SaaS config changed (version hash or content hash)
   - CHANGED: any config difference
```

### Phase 4: Mark Dirty

```
1. ADDED nodes → mark DIRTY (need execution)
2. REMOVED nodes → mark ORPHAN (keep data, remove from graph)
3. For RETAINED nodes:
   a. If edges changed → mark DIRTY
   b. If fields changed → mark DIRTY  
   c. If connection config changed → mark DIRTY
   d. If status is error/pending → mark DIRTY (was going to re-execute anyway)
   e. Otherwise → mark CLEAN
```

### Phase 5: Cascade Dirty

```
For each DIRTY node:
   For each downstream node (BFS/DFS through edges):
     If downstream is CLEAN and COMPLETED:
       Mark as DIRTY (upstream data changed, this node's inputs are stale)
     If downstream is DIRTY:
       Skip (already marked)
     If downstream is ORPHAN:
       Skip (being removed)
```

**Important**: Cascade direction is **downstream only**. A dirty node does not invalidate its upstream nodes (they produced data independently of this node).

**Exception**: Erasure phase with dirty access data. See Phase 6.

### Phase 6: Apply Invalidation

#### Access Phase

For each node:
- **CLEAN + complete**: Preserve. Skip execution. Use existing `access_data`.
- **DIRTY + complete**: Clear `access_data`, `data_for_erasures`. Re-execute.
- **DIRTY + error/pending**: Re-execute (would have re-executed anyway).
- **ADDED**: Create new RequestTask. Execute.
- **ORPHAN**: Keep RequestTask (has historical data). Mark as skipped in new graph. Do not execute.

#### Erasure Phase

For each node:
- **CLEAN + complete (rows_masked > 0)**: Preserve. **Do not re-execute**. Erasure is irreversible.
- **CLEAN + error/pending**: Re-execute normally.
- **DIRTY + complete (rows_masked > 0)**: This is the hard case. The erasure already happened with old `data_for_erasures`. If the access data changed (because the access node was dirty), the erasure targeted potentially wrong rows. Options:
  - **Option A (conservative)**: Log warning. Keep completed erasure. Flag for manual review.
  - **Option B (re-erasure)**: Re-run access for this subtree, then re-run erasure with new data. May mask additional rows that weren't in original set. Cannot un-mask already-masked rows.
  - **Recommended**: Option B with audit logging. The erasure may mask additional rows (ones now discovered via changed access data), but that's the correct behavior. Already-masked rows stay masked (applying masking again is generally idempotent).
- **DIRTY + error/pending**: Re-execute. Needs fresh `data_for_erasures` from re-executed access.
- **ADDED**: Create erasure RequestTask. Execute after access completes.
- **ORPHAN**: Keep RequestTask. Do not execute.

#### Consent Phase

For each node:
- **CLEAN + complete (consent_sent=True)**: Preserve. Consent signals are fire-and-forget.
- **DIRTY or error/pending**: Re-execute. Consent tasks are stateless (they read identity_data, not upstream access_data), so a dirty upstream does not cascade into consent.
- **ADDED**: Create consent RequestTask. Execute.
- **ORPHAN**: Keep. Do not execute.

---

## Cross-Phase Invalidation

The most complex scenario: an access node is dirty, but we're already in the erasure phase.

### Scenario: Access node dirty during erasure reprocess

```
Access graph ran to completion. Erasure partially completed. Request errored.
Admin changes dataset config (adds field reference). Reprocesses.

New graph has:
- access:node_A → DIRTY (edges changed)
- access:node_B → DIRTY (downstream of node_A)
- erasure:node_A → needs fresh data_for_erasures
- erasure:node_B → needs fresh data_for_erasures
- erasure:node_C → CLEAN (completed, no relationship to A/B)
```

**Required flow**:
1. Rebuild access graph
2. Diff → mark access:node_A and access:node_B as DIRTY
3. Re-execute access for node_A and node_B
4. Update `data_for_erasures` on erasure tasks from fresh access data
5. Execute dirty erasure tasks
6. Skip clean erasure tasks (node_C already erased)

**Implementation**: The lifecycle workflow runs the full access `GraphTraversalWorkflow` again. Clean+complete nodes skip at the activity level (check `already_completed` on `NodeInfo`). Only dirty nodes actually execute. Then erasure proceeds with fresh `data_for_erasures` from the re-executed access nodes.

---

## Test Cases

### TC-1: Connection disabled between runs
- **Setup**: Run access. 3 connectors (A→B→C). B fails. Disable B.
- **Reprocess**: Graph rebuilt without B. A is clean+complete. C loses upstream from B.
- **Expected**: A preserved. B becomes orphan (skipped). C re-executes with only A's data (or identity seed).

### TC-2: Connection re-enabled between runs
- **Setup**: Run access with B disabled. A→C completes.
- **Re-enable B** (A→B→C). Reprocess.
- **Expected**: A preserved (clean). B is new node, executes. C is dirty (gained upstream B), re-executes with A+B data.

### TC-3: Field reference added
- **Setup**: A and B are independent (no edges between them). Both complete access.
- **Add reference**: A.email → B.user_email.
- **Reprocess**: B is dirty (gained incoming edge from A). B re-executes with A's data as input.
- **Expected**: A preserved. B re-executed. B's `access_data` changes. B's downstream re-executed.

### TC-4: Field reference removed
- **Setup**: A→B→C. All complete access.
- **Remove reference**: A→B edge removed. B now seeds from identity only.
- **Reprocess**: B is dirty (lost incoming edge). C is dirty (cascade from B).
- **Expected**: A preserved. B re-executed (different query, fewer inputs). C re-executed.

### TC-5: Field added to collection
- **Setup**: A has fields [email, name]. A completes access.
- **Add field**: phone added to A.
- **Reprocess**: A is dirty (field set changed). A's downstream dirty.
- **Expected**: A re-executed (now retrieves phone too). Downstream re-executed.

### TC-6: Field removed from collection
- **Setup**: A has fields [email, name, phone]. B references A.phone. Both complete.
- **Remove field**: phone removed from A.
- **Reprocess**: A is dirty (field set changed). B is dirty (lost input from A.phone).
- **Expected**: A re-executed (no longer retrieves phone). B re-executed (query without phone input).

### TC-7: Erasure completed, then access data changes
- **Setup**: A→B. Access complete for both. Erasure complete for A (rows_masked=5). Erasure pending for B. Request errors.
- **Add reference**: C→A added. Reprocess.
- **Expected**: 
  - Access: C is new (execute). A is dirty (gained upstream C), re-execute. B is dirty (cascade), re-execute.
  - Erasure: A already erased 5 rows. A's `data_for_erasures` now different (may include rows from C). Re-run erasure for A with new data. May mask additional rows. Audit log notes "re-erasure after graph change". B's erasure runs with fresh data.

### TC-8: Manual task, upstream changes
- **Setup**: A→Manual_B→C. A and Manual_B complete (user submitted data). C fails.
- **Add field to A**: Reprocess.
- **Expected**: A is dirty (re-execute). Manual_B: upstream data changed but manual task doesn't use upstream data for retrieval. Manual_B's `access_data` is user-submitted and shouldn't change. However, if Manual_B has new fields in its definition, ManualTaskInstances need recreation. If definition unchanged, Manual_B preserved. C re-executes (was error anyway).

### TC-9: Manual task definition changed
- **Setup**: Manual_B has fields [name, address]. User submitted. Complete.
- **Add field**: Manual_B now has [name, address, phone].
- **Reprocess**: Manual_B is dirty (field set changed). New ManualTaskInstance needed. User must re-submit with phone.
- **Expected**: Manual_B re-executes. Pauses for user input. Downstream dirty.

### TC-10: Polling task in-flight, upstream changes
- **Setup**: A→Polling_B. A complete. Polling_B is mid-poll (status=polling, 2 of 3 sub-requests complete).
- **Add field to A**: Reprocess.
- **Expected**: A is dirty (re-execute). Polling_B is dirty (upstream changed). Must abandon in-flight polling. Sub-requests become orphaned. New polling request sent. External system may have duplicate operations.

### TC-11: Callback task waiting, graph changes
- **Setup**: A→Callback_B. A complete. Callback_B sent initial request, waiting for callback (status=awaiting_processing).
- **Add field to A**: Reprocess.
- **Expected**: A dirty (re-execute). Callback_B dirty (upstream changed). Must re-send initial request. If old callback arrives, must be discarded (check against expected workflow execution state).

### TC-12: Consent phase, access node changes
- **Setup**: Access complete. Consent nodes executing. Consent_A fails.
- **Change access graph**: New reference added to access node X.
- **Reprocess**: Consent nodes don't depend on access data (they use identity_data). Access re-execution for dirty nodes shouldn't affect consent. But if policy determines consent based on data categories found during access, this could change.
- **Expected**: Consent_A re-executes (was error). Other consent nodes preserved. Access dirty nodes re-execute (for data correctness) but don't block consent.

### TC-13: Collection moved to different connection
- **Setup**: Collection "users" on connection A. Access complete.
- **Move**: "users" now on connection B (different connection_key in traversal_details).
- **Reprocess**: Node is dirty (connection_key changed). Same collection address but different connector.
- **Expected**: Re-execute with new connector. May get different data (different database, different credentials).

### TC-14: Property scope changed (IN_SCOPE → TRAVERSAL_ONLY)
- **Setup**: Node A is IN_SCOPE. Access complete. Data in access report.
- **Change**: Node A becomes TRAVERSAL_ONLY.
- **Reprocess**: A is dirty (property scope changed). A should still execute (provides FK data) but its data should not appear in access report and should not generate erasure tasks.
- **Expected**: A re-executes. Access report regenerated without A's data. Erasure task for A skipped.

### TC-15: No changes, just retry errored tasks
- **Setup**: A→B→C. A complete. B error. C pending (cascaded error).
- **No config changes**: Reprocess.
- **Expected**: Diff shows no changes. A clean+complete (preserved). B dirty (error status). C dirty (error status). B and C re-execute. This is the simple retry case.

### TC-16: SaaS config version bump
- **Setup**: Stripe connector, access complete.
- **SaaS config update**: New endpoint parameter added, or pagination changed.
- **Reprocess**: Node dirty (SaaS config content changed).
- **Expected**: Re-execute with new SaaS config. May retrieve different data.

### TC-17: Multiple independent subtrees, one dirty
- **Setup**: Identity seeds A and D independently. A→B→C and D→E→F. C errors.
- **Change**: Add field to D.
- **Reprocess**: 
  - A,B clean+complete. C dirty (error).
  - D dirty (field change). E dirty (cascade). F dirty (cascade).
- **Expected**: A,B preserved. C re-executes. D,E,F all re-execute. The two subtrees are independent.

### TC-18: Erasure ordering (erase_after) change
- **Setup**: Erasure for A and B. No erase_after deps. Both can run in parallel. A complete.
- **Change**: B gets `erase_after: [A]`.
- **Reprocess**: Graph topology changed (erasure ordering). B now depends on A.
- **Expected**: A already complete (preserved). B re-executes (was pending/error anyway). New ordering respected.

### TC-19: Bidirectional edge changed to directional
- **Setup**: A↔B (bidirectional). Access complete.
- **Change**: A→B (directional, A feeds B but not reverse).
- **Reprocess**: B's incoming edges changed. B is dirty.
- **Expected**: B re-executes. If A was using data from B (via the bidirectional edge), A would also need re-execution. Diff must check both incoming and outgoing edges.

### TC-20: Identity field added to new collection
- **Setup**: Graph seeded by A.email. A→B→C. All complete.
- **Change**: New collection D added with `identity: phone`. Privacy request has phone in identity data.
- **Reprocess**: D is new node (ADDED). If D has references to existing nodes, those become dirty.
- **Expected**: D executes. Any node with new edges from/to D re-executes. Existing clean nodes without new edges preserved.

---

## Design Decisions

1. **SaaS config diff granularity**: **Hash entire config JSON.** Any change to SaaS config marks node dirty. Simpler, safer, and avoids subtle bugs from partial diffing. Over-invalidation is acceptable since re-execution is cheap relative to missing a real change.

2. **Manual task re-submission UX**: **Reuse `requires_input` status.** No new status. Admin sees invalidated manual tasks in the same queue as first-time submissions. Keeps status machine simple.

3. **Polling task abandonment**: **Abandon silently.** Stop polling on our side. External system finishes or times out on its own. No cancel API needed. Log the abandonment for debugging.

4. **Erasure idempotency**: **Re-masking is safe for all strategies.** Run erasure again on full dataset. Already-masked rows get re-masked (harmless). NULL_REWRITE and HASH are strictly idempotent. RANDOM_STRING_REWRITE produces different values but data is already masked. Simpler than diffing old vs new rows.

5. **Diff storage**: **Structured logs + Temporal workflow memo.** Log invalidation decisions as structured log entries (searchable in log aggregator). Attach diff summary as Temporal workflow memo (visible in Temporal UI alongside workflow history). No DB persistence needed.

6. **Partial access re-execution**: **Skip at activity level.** `GraphTraversalWorkflow` runs all nodes. Each `NodeExecutionWorkflow` checks `already_completed` flag on `NodeInfo` and returns early if clean+complete. Keeps workflow DAG shape consistent, simplifies dependency tracking, and shows full graph in Temporal UI.

7. **Concurrent reprocess**: **Queue via Temporal native workflow ID reuse policy.** Second reprocess attempt queues behind running workflow. Temporal handles ordering. Second run starts after first completes or fails, then rebuilds graph fresh (picking up any additional changes made while first run was executing).
