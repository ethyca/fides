"""Purpose-Based Access Control (PBAC) evaluation service.

Import types and pure functions directly::

    from fides.service.pbac.types import RawQueryLogEntry, EvaluationResult
    from fides.service.pbac.evaluate import evaluate_access
    from fides.service.pbac.service import PBACEvaluationService

The service module (PBACEvaluationService, InProcessPBACEvaluationService)
requires Redis/Celery deps and should be imported explicitly from
``fides.service.pbac.service``.
"""
