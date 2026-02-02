"""
Base validation rule classes for settings validation.

This module defines the core abstractions for validation rules:
- ValidationSeverity: ERROR (blocks), WARNING (logs), INFO (informational)
- ValidationResult: The outcome of running a validation rule
- ValidationRule: Abstract base class for all rules
- PrerequisiteRule: Setting A requires Setting B
- ConflictRule: Settings A and B conflict
- DBStateRule: Setting requires specific DB state
- RequiredSettingRule: Setting must be set
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import reduce
from typing import Any, Callable, List, Optional, Set, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from fides.config import FidesConfig


class ValidationSeverity(Enum):
    """Severity level for validation results."""

    ERROR = "error"  # Blocks startup/operation
    WARNING = "warning"  # Logs warning, continues
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """The result of running a validation rule."""

    passed: bool
    severity: ValidationSeverity
    message: str
    rule_name: str
    details: Optional[dict] = None

    def __str__(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        return f"[{self.severity.value.upper()}] {self.rule_name}: {status} - {self.message}"


def get_nested_attr(obj: Any, path: str) -> Any:
    """
    Get a nested attribute from an object using dot notation.

    Example:
        get_nested_attr(config, "consent.tcf_enabled") -> config.consent.tcf_enabled
    """
    try:
        return reduce(getattr, path.split("."), obj)
    except AttributeError:
        return None


class ValidationRule(ABC):
    """
    Abstract base class for all validation rules.

    Rules declare what settings and entities they care about via
    `relevant_settings` and `relevant_entities`. The ValidationManager
    uses these to determine which rules to run:
    - Startup: ALL rules run
    - Config update: Only rules whose relevant_settings overlap with changes
    - DB change: Only rules whose relevant_entities include the entity type
    """

    name: str
    description: str
    severity: ValidationSeverity

    # What this rule cares about (subscription model)
    relevant_settings: Set[str]
    relevant_entities: Set[str]

    def __init__(
        self,
        name: str,
        description: str = "",
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        relevant_settings: Optional[Set[str]] = None,
        relevant_entities: Optional[Set[str]] = None,
    ):
        self.name = name
        self.description = description
        self.severity = severity
        self.relevant_settings = relevant_settings or set()
        self.relevant_entities = relevant_entities or set()

    @abstractmethod
    def validate(
        self,
        config: "FidesConfig",
        db: Optional["Session"] = None,
    ) -> ValidationResult:
        """
        Execute the validation rule.

        Args:
            config: The FidesConfig to validate
            db: Optional database session for DB state validation

        Returns:
            ValidationResult indicating pass/fail and details
        """
        pass

    def _make_result(
        self,
        passed: bool,
        message: str,
        details: Optional[dict] = None,
    ) -> ValidationResult:
        """Helper to create a ValidationResult with this rule's properties."""
        return ValidationResult(
            passed=passed,
            severity=self.severity,
            message=message,
            rule_name=self.name,
            details=details,
        )


class PrerequisiteRule(ValidationRule):
    """
    Validates that a prerequisite setting is enabled before a dependent setting.

    Example:
        PrerequisiteRule(
            name="ac_requires_tcf",
            prerequisite_path="consent.tcf_enabled",
            dependent_path="consent.ac_enabled",
            message="AC mode cannot be enabled unless TCF mode is also enabled",
        )

    This rule fails if the dependent is enabled but the prerequisite is not met.
    """

    def __init__(
        self,
        name: str,
        prerequisite_path: str,
        dependent_path: str,
        prerequisite_value: Any = True,
        message: Optional[str] = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        # Auto-populate relevant_settings from the paths
        super().__init__(
            name=name,
            description=message or f"{dependent_path} requires {prerequisite_path}={prerequisite_value}",
            severity=severity,
            relevant_settings={prerequisite_path, dependent_path},
        )
        self.prerequisite_path = prerequisite_path
        self.dependent_path = dependent_path
        self.prerequisite_value = prerequisite_value
        self.message = message

    def validate(
        self,
        config: "FidesConfig",
        db: Optional["Session"] = None,
    ) -> ValidationResult:
        """Check that prerequisite is met when dependent is enabled."""
        prereq_value = get_nested_attr(config, self.prerequisite_path)
        dependent_value = get_nested_attr(config, self.dependent_path)

        # If the dependent setting is enabled/truthy but prerequisite is not met
        if dependent_value and prereq_value != self.prerequisite_value:
            return self._make_result(
                passed=False,
                message=self.message
                or f"{self.dependent_path} is enabled but requires {self.prerequisite_path}={self.prerequisite_value}",
                details={
                    "prerequisite_path": self.prerequisite_path,
                    "prerequisite_expected": self.prerequisite_value,
                    "prerequisite_actual": prereq_value,
                    "dependent_path": self.dependent_path,
                    "dependent_value": dependent_value,
                },
            )

        return self._make_result(
            passed=True,
            message=f"Prerequisite check passed for {self.dependent_path}",
        )


class ConflictRule(ValidationRule):
    """
    Detects conflicting or invalid combinations of settings.

    Example:
        ConflictRule(
            name="root_user_credentials_complete",
            setting_paths=["security.root_username", "security.root_password"],
            conflict_condition=lambda values: bool(values[0]) != bool(values[1]),
            message="Both root_username and root_password must be set if either is set",
        )

    The conflict_condition receives a list of setting values in the same order
    as setting_paths. It should return True if there IS a conflict.
    """

    def __init__(
        self,
        name: str,
        setting_paths: List[str],
        conflict_condition: Callable[[List[Any]], bool],
        message: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        super().__init__(
            name=name,
            description=message,
            severity=severity,
            relevant_settings=set(setting_paths),
        )
        self.setting_paths = setting_paths
        self.conflict_condition = conflict_condition
        self.message = message

    def validate(
        self,
        config: "FidesConfig",
        db: Optional["Session"] = None,
    ) -> ValidationResult:
        """Check for conflicting setting combinations."""
        values = [get_nested_attr(config, path) for path in self.setting_paths]

        if self.conflict_condition(values):
            return self._make_result(
                passed=False,
                message=self.message,
                details={
                    "setting_paths": self.setting_paths,
                    "values": values,
                },
            )

        return self._make_result(
            passed=True,
            message=f"No conflict detected for {self.setting_paths}",
        )


class DBStateRule(ValidationRule):
    """
    Validates that database state matches setting requirements.

    Example:
        DBStateRule(
            name="tcf_requires_gvl",
            setting_path="consent.tcf_enabled",
            entity_types=["GvlPurpose"],
            check_fn=lambda db, config: db.query(GvlPurpose).count() > 0,
            message="TCF is enabled but no GVL data exists in database",
        )

    The check_fn receives the database session and config, and should return
    True if the DB state is valid for the current settings.
    """

    def __init__(
        self,
        name: str,
        setting_path: str,
        entity_types: List[str],
        check_fn: Callable[["Session", "FidesConfig"], bool],
        message: str,
        setting_value: Any = True,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        super().__init__(
            name=name,
            description=message,
            severity=severity,
            relevant_settings={setting_path},
            relevant_entities=set(entity_types),
        )
        self.setting_path = setting_path
        self.setting_value = setting_value
        self.check_fn = check_fn
        self.message = message

    def validate(
        self,
        config: "FidesConfig",
        db: Optional["Session"] = None,
    ) -> ValidationResult:
        """Check that DB state matches config requirements."""
        # If no DB session, skip gracefully
        if db is None:
            logger.debug(f"Skipping DB state rule {self.name} - no database session")
            return self._make_result(
                passed=True,
                message=f"Skipped {self.name} - no database session available",
                details={"skipped": True, "reason": "no_db_session"},
            )

        # Check if the setting that triggers this rule is active
        setting_value = get_nested_attr(config, self.setting_path)
        if setting_value != self.setting_value:
            # Setting is not active, rule doesn't apply
            return self._make_result(
                passed=True,
                message=f"Rule {self.name} not applicable - {self.setting_path} is not {self.setting_value}",
            )

        # Run the DB state check
        try:
            is_valid = self.check_fn(db, config)
        except Exception as e:
            logger.error(f"Error running DB state check {self.name}: {e}")
            return self._make_result(
                passed=False,
                message=f"Error checking DB state: {e}",
                details={"error": str(e)},
            )

        if not is_valid:
            return self._make_result(
                passed=False,
                message=self.message,
                details={
                    "setting_path": self.setting_path,
                    "setting_value": setting_value,
                },
            )

        return self._make_result(
            passed=True,
            message=f"DB state check passed for {self.name}",
        )


class RequiredSettingRule(ValidationRule):
    """
    Validates that a required setting is configured.

    Example:
        RequiredSettingRule(
            name="encryption_key_required",
            setting_path="security.app_encryption_key",
            message="security.app_encryption_key must be set",
        )

    Optionally, can specify a condition that must be true for the requirement
    to apply (e.g., only required when another setting is enabled).
    """

    def __init__(
        self,
        name: str,
        setting_path: str,
        message: str,
        condition_path: Optional[str] = None,
        condition_value: Any = True,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        relevant = {setting_path}
        if condition_path:
            relevant.add(condition_path)

        super().__init__(
            name=name,
            description=message,
            severity=severity,
            relevant_settings=relevant,
        )
        self.setting_path = setting_path
        self.message = message
        self.condition_path = condition_path
        self.condition_value = condition_value

    def validate(
        self,
        config: "FidesConfig",
        db: Optional["Session"] = None,
    ) -> ValidationResult:
        """Check that the required setting is configured."""
        # If there's a condition, check it first
        if self.condition_path:
            condition_actual = get_nested_attr(config, self.condition_path)
            if condition_actual != self.condition_value:
                # Condition not met, requirement doesn't apply
                return self._make_result(
                    passed=True,
                    message=f"Requirement for {self.setting_path} not applicable - condition not met",
                )

        value = get_nested_attr(config, self.setting_path)

        # Check if value is "empty" (None, empty string, etc.)
        is_set = value is not None and value != ""

        if not is_set:
            return self._make_result(
                passed=False,
                message=self.message,
                details={
                    "setting_path": self.setting_path,
                    "value": value,
                },
            )

        return self._make_result(
            passed=True,
            message=f"Required setting {self.setting_path} is configured",
        )
