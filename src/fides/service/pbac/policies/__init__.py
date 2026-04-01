"""Access policy evaluation interface for Policies v2.

Defines the Protocol boundary between PBAC enforcement and the
Policy v2 evaluation engine.  PBAC checks purpose overlap first;
when purposes do NOT match, the AccessPolicyEvaluator is consulted.
"""

from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    AccessPolicyEvaluator,
    EvaluatedPolicyInfo,
    PolicyAction,
    PolicyDecision,
    PolicyEvaluationResult,
)
from fides.service.pbac.policies.noop import NoOpPolicyEvaluator

__all__ = [
    "AccessEvaluationRequest",
    "AccessPolicyEvaluator",
    "EvaluatedPolicyInfo",
    "NoOpPolicyEvaluator",
    "PolicyAction",
    "PolicyDecision",
    "PolicyEvaluationResult",
]
