"""
ValidationManager - Central manager for settings validation.

The ValidationManager is responsible for:
- Maintaining a registry of validation rules
- Running validation at startup (all rules)
- Running validation on config updates (relevant rules only)
- Running validation on DB changes (relevant rules only)
"""

from typing import Any, List, Optional, Set, TYPE_CHECKING

from loguru import logger

from fides.config.validation.rules import (
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from fides.config import FidesConfig


class ValidationManager:
    """
    Central manager for settings validation.

    Uses a registry pattern where rules self-register. The manager then
    runs appropriate rules based on the validation context:
    - Startup: ALL rules run
    - Config update: Only rules whose relevant_settings intersect with changes
    - DB change: Only rules whose relevant_entities include the entity type

    Usage:
        # Register rules (typically at module load time)
        ValidationManager.register(
            PrerequisiteRule(
                name="ac_requires_tcf",
                prerequisite_path="consent.tcf_enabled",
                dependent_path="consent.ac_enabled",
            )
        )

        # Validate at startup
        results = ValidationManager.validate_startup(config, db)

        # Validate config update
        results = ValidationManager.validate_config_update(
            config, {"consent.tcf_enabled"}, db
        )
    """

    _rules: List[ValidationRule] = []

    @classmethod
    def register(cls, rule: ValidationRule) -> None:
        """
        Register a validation rule.

        Rules can be registered from anywhere (Fides core, Fidesplus, etc.)
        and will be included in validation runs.
        """
        # Avoid duplicate registration
        if any(r.name == rule.name for r in cls._rules):
            logger.debug(f"Rule {rule.name} already registered, skipping")
            return

        logger.debug(f"Registering validation rule: {rule.name}")
        cls._rules.append(rule)

    @classmethod
    def unregister(cls, rule_name: str) -> bool:
        """
        Unregister a validation rule by name.

        Returns True if the rule was found and removed, False otherwise.
        """
        for i, rule in enumerate(cls._rules):
            if rule.name == rule_name:
                cls._rules.pop(i)
                logger.debug(f"Unregistered validation rule: {rule_name}")
                return True
        return False

    @classmethod
    def clear_rules(cls) -> None:
        """
        Clear all registered rules.

        Primarily useful for testing.
        """
        cls._rules = []

    @classmethod
    def get_rules(cls) -> List[ValidationRule]:
        """Get all registered rules."""
        return cls._rules.copy()

    @classmethod
    def validate_startup(
        cls,
        config: "FidesConfig",
        db: Optional["Session"] = None,
    ) -> List[ValidationResult]:
        """
        Run ALL validation rules on startup.

        This is the comprehensive validation that should catch any
        misconfigurations before the application fully starts.

        Args:
            config: The FidesConfig to validate
            db: Optional database session for DB state validation

        Returns:
            List of ValidationResults from all rules
        """
        logger.info(f"Running startup validation with {len(cls._rules)} rules")
        results = []

        for rule in cls._rules:
            try:
                result = rule.validate(config, db)
                results.append(result)

                if not result.passed:
                    if result.severity == ValidationSeverity.ERROR:
                        logger.error(f"Validation failed: {result}")
                    elif result.severity == ValidationSeverity.WARNING:
                        logger.warning(f"Validation warning: {result}")
                    else:
                        logger.info(f"Validation info: {result}")
            except Exception as e:
                logger.error(f"Error running validation rule {rule.name}: {e}")
                results.append(
                    ValidationResult(
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Error executing rule: {e}",
                        rule_name=rule.name,
                        details={"error": str(e)},
                    )
                )

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        logger.info(f"Startup validation complete: {passed} passed, {failed} failed")

        return results

    @classmethod
    def validate_config_update(
        cls,
        config: "FidesConfig",
        changed_settings: Set[str],
        db: Optional["Session"] = None,
    ) -> List[ValidationResult]:
        """
        Run only rules relevant to the changed settings.

        This is used when configuration is updated via API to validate
        just the affected rules, not the entire configuration.

        Args:
            config: The FidesConfig with proposed changes applied
            changed_settings: Set of setting paths that were changed
            db: Optional database session for DB state validation

        Returns:
            List of ValidationResults from relevant rules only
        """
        # Find rules whose relevant_settings intersect with changed settings
        relevant_rules = [
            rule
            for rule in cls._rules
            if rule.relevant_settings & changed_settings
        ]

        logger.debug(
            f"Running config update validation: {len(relevant_rules)} rules "
            f"relevant to changes in {changed_settings}"
        )

        results = []
        for rule in relevant_rules:
            try:
                result = rule.validate(config, db)
                results.append(result)
            except Exception as e:
                logger.error(f"Error running validation rule {rule.name}: {e}")
                results.append(
                    ValidationResult(
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Error executing rule: {e}",
                        rule_name=rule.name,
                        details={"error": str(e)},
                    )
                )

        return results

    @classmethod
    def validate_db_change(
        cls,
        config: "FidesConfig",
        entity_type: str,
        operation: str,
        entity: Any,
        db: "Session",
    ) -> List[ValidationResult]:
        """
        Run only rules relevant to this entity type.

        This is used when database entities are created/updated/deleted
        to validate that the change is consistent with current settings.

        Args:
            config: The current FidesConfig
            entity_type: The type of entity being changed (e.g., "GvlPurpose")
            operation: The operation ("create", "update", "delete")
            entity: The entity being changed
            db: Database session

        Returns:
            List of ValidationResults from relevant rules only
        """
        # Find rules whose relevant_entities include this entity type
        relevant_rules = [
            rule
            for rule in cls._rules
            if entity_type in rule.relevant_entities
        ]

        logger.debug(
            f"Running DB change validation: {len(relevant_rules)} rules "
            f"relevant to {operation} on {entity_type}"
        )

        results = []
        for rule in relevant_rules:
            try:
                result = rule.validate(config, db)
                results.append(result)
            except Exception as e:
                logger.error(f"Error running validation rule {rule.name}: {e}")
                results.append(
                    ValidationResult(
                        passed=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Error executing rule: {e}",
                        rule_name=rule.name,
                        details={"error": str(e)},
                    )
                )

        return results

    @classmethod
    def validate_all(
        cls,
        config: "FidesConfig",
        db: Optional["Session"] = None,
    ) -> List[ValidationResult]:
        """
        Run all validation rules (alias for validate_startup).

        This is useful for on-demand validation via API endpoint.
        """
        return cls.validate_startup(config, db)

    @classmethod
    def get_errors(cls, results: List[ValidationResult]) -> List[ValidationResult]:
        """Filter results to only ERROR severity failures."""
        return [
            r
            for r in results
            if not r.passed and r.severity == ValidationSeverity.ERROR
        ]

    @classmethod
    def get_warnings(cls, results: List[ValidationResult]) -> List[ValidationResult]:
        """Filter results to only WARNING severity failures."""
        return [
            r
            for r in results
            if not r.passed and r.severity == ValidationSeverity.WARNING
        ]

    @classmethod
    def has_errors(cls, results: List[ValidationResult]) -> bool:
        """Check if any results are ERROR severity failures."""
        return len(cls.get_errors(results)) > 0

    @classmethod
    def format_errors(cls, results: List[ValidationResult]) -> str:
        """Format error results as a human-readable string."""
        errors = cls.get_errors(results)
        if not errors:
            return ""
        return "\n".join(f"- {e.message}" for e in errors)
