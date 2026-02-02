"""
Settings validation framework for Fides.

This module provides a composable validation system for configuration settings
that validates on startup, during API updates, and when related DB items change.

The design follows established patterns:
- Fail-Fast Pattern: Validate at startup, fail immediately if invalid
- Rule Engine Pattern: Discrete, composable validation rules
- Registry Pattern: Rules self-register with a central manager
- Subscription Pattern: Rules declare what settings/entities they care about
"""

from fides.config.validation.manager import ValidationManager
from fides.config.validation.rules import (
    ConflictRule,
    DBStateRule,
    PrerequisiteRule,
    RequiredSettingRule,
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
)

# Import fides_rules to register built-in rules
# This ensures rules are registered when the validation module is imported
from fides.config.validation import fides_rules as _fides_rules  # noqa: F401

__all__ = [
    "ValidationManager",
    "ValidationRule",
    "ValidationResult",
    "ValidationSeverity",
    "PrerequisiteRule",
    "ConflictRule",
    "DBStateRule",
    "RequiredSettingRule",
]
