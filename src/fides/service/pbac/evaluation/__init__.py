"""Backward-compatible re-exports.

Types moved to ``fides.service.pbac.types``.
Service moved to ``fides.service.pbac.service``.

Import directly from the canonical modules instead of this shim.
"""

from fides.service.pbac.types import (
    EvaluationGap,
    EvaluationResult,
    EvaluationViolation,
)

__all__ = [
    "EvaluationGap",
    "EvaluationResult",
    "EvaluationViolation",
]


def __getattr__(name: str) -> object:
    """Lazy imports for service classes that pull in Redis/Celery deps."""
    if name in ("PBACEvaluationService", "InProcessPBACEvaluationService"):
        from fides.service.pbac.service import (
            InProcessPBACEvaluationService,
            PBACEvaluationService,
        )

        return {
            "PBACEvaluationService": PBACEvaluationService,
            "InProcessPBACEvaluationService": InProcessPBACEvaluationService,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
