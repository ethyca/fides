"""Purpose-Based Access Control (PBAC) evaluation service.

Import types directly::

    from fides.service.pbac.types import RawQueryLogEntry, EvaluationRecord
    from fides.service.pbac.service import PBACEvaluationService

All evaluation logic runs in Go via the libpbac shared library.
Python-side entry points:

    from fides.service.pbac.engine import evaluate_pipeline, evaluate_purpose
"""
