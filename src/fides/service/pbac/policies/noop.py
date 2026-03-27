"""No-op policy evaluator -- default until Policy v2 is implemented."""

from __future__ import annotations

from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    PolicyDecision,
    PolicyEvaluationResult,
)


class NoOpPolicyEvaluator:
    """Always returns NO_DECISION.

    Used as the default evaluator so that all PBAC violations are
    recorded as-is.  Replace with the real Policy v2 evaluator by
    swapping the factory in deps.py.
    """

    def evaluate(self, request: AccessEvaluationRequest) -> PolicyEvaluationResult:
        return PolicyEvaluationResult(decision=PolicyDecision.NO_DECISION)
