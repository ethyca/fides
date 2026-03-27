# Policy v2 Implementation Guide

This guide covers how to implement the Policy v2 evaluation engine. The interface is defined, the integration point is wired up, and a `NoOpPolicyEvaluator` is in place. The next step is to replace the no-op with real policy matching and evaluation.

## How it fits in

```
SQL query arrives
    |
    v
PBAC engine checks purpose overlap
    |
    +-- purposes match --> COMPLIANT (policies never consulted)
    |
    +-- purposes DON'T match --> policy evaluator runs here
            |
            v
        AccessPolicyEvaluator.evaluate(request)
            |
            +-- ALLOW      --> violation suppressed
            +-- DENY        --> violation confirmed
            +-- NO_DECISION --> violation confirmed (default today)
```

PBAC always runs first. The policy evaluator is only called when purposes don't overlap. An `ALLOW` result suppresses the violation. Anything else keeps it.

## The interface to implement

```python
# fides/service/pbac/policies/interface.py

class AccessPolicyEvaluator(Protocol):
    def evaluate(self, request: AccessEvaluationRequest) -> PolicyEvaluationResult: ...
```

### Input: `AccessEvaluationRequest`

Fields available to the evaluator:

```python
@dataclass(frozen=True)
class AccessEvaluationRequest:
    # Who is accessing (from the PBAC violation)
    consumer_id: str                    # fides ID or email if unresolved
    consumer_name: str
    consumer_purposes: frozenset[str]   # purposes the consumer declared

    # What they're accessing
    dataset_key: str
    dataset_purposes: frozenset[str]    # purposes declared on the dataset
    collection: str | None              # specific collection, if known

    # For policy match resolution (enrichment from the consumer's system)
    system_fides_key: str | None        # the consumer's system in fides
    data_uses: tuple[str, ...]          # from system privacy declarations
    data_categories: tuple[str, ...]    # from system privacy declarations
    data_subjects: tuple[str, ...]      # from system privacy declarations

    # Runtime context for unless conditions
    context: dict[str, Any]             # e.g. {"environment": {"geo_location": "US-CA"},
                                        #        "subject": {"email": "user@example.com"}}
```

### Output: `PolicyEvaluationResult`

```python
@dataclass
class PolicyEvaluationResult:
    decision: PolicyDecision            # ALLOW, DENY, or NO_DECISION
    decisive_policy_key: str | None     # which policy decided (None if NO_DECISION)
    decisive_policy_priority: int | None
    unless_triggered: bool              # True if the decisive policy's unless block fired
    evaluated_policies: list[EvaluatedPolicyInfo]  # audit trail of all matched policies
    action: PolicyAction | None         # denial message from the decisive policy
    reason: str | None                  # human-readable explanation
```

## What you need to build

### 1. Policy storage

Policies need to be stored and retrievable. Each policy looks like:

```yaml
fides_key: ccpa_sale_blocker
decision: ALLOW                    # or DENY
priority: 100                      # higher = evaluated first
enabled: true
controls: [ccpa_compliance]        # grouping (organizational, not evaluated)

match:                             # which declarations this applies to
  data_use:
    any: [marketing.advertising]
  data_category:
    all: [user.contact.email]

unless:                            # conditions that invert the decision
  - type: consent
    privacy_notice_key: ccpa_do_not_sell
    requirement: opt_out
  - type: geo_location
    field: environment.geo_location
    operator: in
    values: ["US-CA"]

action:                            # what to show when blocking
  message: "User opted out of data sales."
```

For now, follow the `RedisRepository` pattern used by consumers and purposes (`fides/service/pbac/redis_repository.py`). This keeps things consistent with the rest of the PBAC layer while we settle on the final models. We'll migrate to Postgres once the models are finalized.

### 2. Match evaluation

The `match` block determines which policies apply to a given request. All dimensions are AND'd.

**Built-in dimensions** (match against `AccessEvaluationRequest` fields):

| Match dimension | Request field | Operator |
|----------------|---------------|----------|
| `data_use` | `request.data_uses` | `any` or `all` |
| `data_category` | `request.data_categories` | `any` or `all` |
| `data_subject` | `request.data_subjects` | `any` or `all` |
| `<custom_taxonomy>` | looked up via taxonomy key | `any` or `all` |

**Hierarchical matching**: `user.contact` matches `user.contact.email` (child) but not `user` (parent).

**Empty match** (`match: {}`) matches everything -- used for catch-all default policies.

### 3. Unless evaluation

The `unless` block defines conditions that **invert** the decision when ALL conditions are met (AND'd).

Behavior:
- ALLOW + unless triggered = **DENY** (decisive, stops evaluation)
- DENY + unless triggered = **suppressed** (not decisive, evaluation continues)

Condition types to implement:

| Type | What it checks | Where the data comes from |
|------|---------------|--------------------------|
| `consent` | Privacy notice opt-in/opt-out status | `request.context["subject"]` -> consent DB lookup |
| `geo_location` | Geographic location of the request | `request.context["environment"]["geo_location"]` |
| `data_flow` | Ingress/egress system relationships | System's ingress/egress config in fides |

### 4. Evaluation algorithm

```python
def evaluate(self, request: AccessEvaluationRequest) -> PolicyEvaluationResult:
    # 1. Load all enabled policies, sorted by priority (highest first)
    policies = self._policy_store.get_enabled_sorted_by_priority()

    # 2. Find matching policies
    evaluated = []
    for policy in policies:
        if not self._matches(policy, request):
            continue

        # 3. Check unless conditions
        unless_triggered = self._evaluate_unless(policy, request)

        if unless_triggered:
            if policy.decision == "ALLOW":
                # ALLOW inverted to DENY -- decisive, stop
                return PolicyEvaluationResult(
                    decision=PolicyDecision.DENY,
                    decisive_policy_key=policy.fides_key,
                    decisive_policy_priority=policy.priority,
                    unless_triggered=True,
                    action=policy.action,
                    evaluated_policies=evaluated,
                )
            else:
                # DENY suppressed -- not decisive, continue
                evaluated.append(EvaluatedPolicyInfo(
                    policy_key=policy.fides_key,
                    priority=policy.priority,
                    matched=True,
                    result="SUPPRESSED",
                    unless_triggered=True,
                ))
                continue
        else:
            # Decision stands as-is -- decisive, stop
            return PolicyEvaluationResult(
                decision=PolicyDecision(policy.decision),
                decisive_policy_key=policy.fides_key,
                decisive_policy_priority=policy.priority,
                unless_triggered=False,
                action=policy.action if policy.decision == "DENY" else None,
                evaluated_policies=evaluated,
            )

    # 4. No policy matched
    return PolicyEvaluationResult(decision=PolicyDecision.NO_DECISION)
```

### 5. Wire it up

The `NoOpPolicyEvaluator` gets replaced in the evaluation service. `InProcessPBACEvaluationService.__init__` in `fides/service/pbac/service.py` accepts a `policy_evaluator` parameter:

```python
# Before (current default):
self._policy_evaluator = policy_evaluator or NoOpPolicyEvaluator()

# After (with the real implementation):
self._policy_evaluator = policy_evaluator or PolicyV2Evaluator(policy_store)
```

The DI factory in fidesplus `deps.py` creates the evaluation service:

```python
def get_pbac_evaluation_service() -> PBACEvaluationService:
    return InProcessPBACEvaluationService()  # uses NoOp by default
```

Update it to inject the real evaluator:

```python
def get_pbac_evaluation_service() -> PBACEvaluationService:
    return InProcessPBACEvaluationService(
        policy_evaluator=PolicyV2Evaluator(policy_store=...)
    )
```

## Files to create

| File | Purpose |
|------|---------|
| `fides/service/pbac/policies/evaluator.py` | `PolicyV2Evaluator` class |
| `fides/service/pbac/policies/store.py` | Policy storage (follow `RedisRepository` pattern from `fides/service/pbac/redis_repository.py`) |
| `fides/service/pbac/policies/match.py` | Match block evaluation (hierarchy, operators) |
| `fides/service/pbac/policies/unless.py` | Unless condition evaluation (consent, geo, data_flow) |
| `fides/service/pbac/policies/entities.py` | Policy entity dataclass (follow `DataPurposeEntity` pattern) |

## Files that shouldn't need changes

| File | Why |
|------|-----|
| `fides/service/pbac/evaluate.py` | PBAC engine -- runs before the policy evaluator |
| `fides/service/pbac/service.py` | Orchestrator -- calls the evaluator automatically |
| `fides/service/pbac/types.py` | Shared types -- already defined |
| `fides/service/pbac/policies/interface.py` | The contract -- already defined |

## Testing

```python
from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    PolicyDecision,
    PolicyEvaluationResult,
)

def test_allow_policy_suppresses_violation():
    evaluator = PolicyV2Evaluator(policy_store=InMemoryPolicyStore([
        Policy(fides_key="allow_marketing", decision="ALLOW", priority=100,
               match={"data_use": {"any": ["marketing.advertising"]}}),
    ]))
    request = AccessEvaluationRequest(
        consumer_id="c1",
        consumer_name="Analytics Team",
        consumer_purposes=frozenset({"marketing"}),
        dataset_key="ds1",
        dataset_purposes=frozenset({"billing"}),
        data_uses=("marketing.advertising",),
    )
    result = evaluator.evaluate(request)
    assert result.decision == PolicyDecision.ALLOW
    assert result.decisive_policy_key == "allow_marketing"


def test_no_matching_policy_returns_no_decision():
    evaluator = PolicyV2Evaluator(policy_store=InMemoryPolicyStore([]))
    request = AccessEvaluationRequest(
        consumer_id="c1",
        consumer_name="Test",
        consumer_purposes=frozenset(),
        dataset_key="ds1",
        dataset_purposes=frozenset(),
    )
    result = evaluator.evaluate(request)
    assert result.decision == PolicyDecision.NO_DECISION


def test_unless_inverts_allow_to_deny():
    evaluator = PolicyV2Evaluator(policy_store=InMemoryPolicyStore([
        Policy(fides_key="ccpa_blocker", decision="ALLOW", priority=100,
               match={"data_use": {"any": ["marketing"]}},
               unless=[{"type": "consent", "privacy_notice_key": "do_not_sell",
                        "requirement": "opt_out"}]),
    ]))
    request = AccessEvaluationRequest(
        consumer_id="c1",
        consumer_name="Test",
        consumer_purposes=frozenset({"marketing"}),
        dataset_key="ds1",
        dataset_purposes=frozenset({"billing"}),
        data_uses=("marketing",),
        context={"subject": {"email": "user@example.com"}},
    )
    # Mock consent lookup to return opt_out=True
    result = evaluator.evaluate(request)
    assert result.decision == PolicyDecision.DENY
    assert result.unless_triggered is True
```

## PRD reference

The full policy schema, evaluation algorithm, and examples are in the Confluence PRD:
[Fides Policy Engine v2 Schema Redesign](https://ethyca.atlassian.net/wiki/spaces/PM/pages/4244275202)

Key sections:
- Section 2: Policy schema (match, unless, action, controls)
- Section 3: Evaluation algorithm (priority-based, first-decisive-match-wins)
- Section 4: Worked examples with evaluation walkthroughs
