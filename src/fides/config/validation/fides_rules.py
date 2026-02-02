"""
Built-in Fides validation rules.

This module registers the core validation rules for Fides settings.
Rules are registered at module import time, so importing this module
(or the parent validation package) will register all rules.

These rules cover:
- Prerequisite settings (A requires B)
- Required settings (must be configured)
- Conflict detection (invalid combinations)
- DB state validation (settings require DB state)
"""

from fides.config.validation.manager import ValidationManager
from fides.config.validation.rules import (
    ConflictRule,
    PrerequisiteRule,
    RequiredSettingRule,
    ValidationSeverity,
)


def register_fides_rules() -> None:
    """
    Register all built-in Fides validation rules.

    This function is called automatically when the validation module is imported,
    but can also be called explicitly if needed.
    """
    _register_consent_rules()
    _register_execution_rules()
    _register_notification_rules()
    _register_security_rules()
    _register_redis_rules()
    _register_database_rules()


def _register_consent_rules() -> None:
    """Register consent-related validation rules."""

    # AC mode requires TCF mode
    # Note: This is also validated by Pydantic, but we include it here
    # for completeness and to demonstrate the pattern
    ValidationManager.register(
        PrerequisiteRule(
            name="ac_requires_tcf",
            prerequisite_path="consent.tcf_enabled",
            dependent_path="consent.ac_enabled",
            message="AC mode cannot be enabled unless TCF mode is also enabled",
        )
    )

    # Override vendor purposes requires TCF mode
    ValidationManager.register(
        PrerequisiteRule(
            name="override_vendor_purposes_requires_tcf",
            prerequisite_path="consent.tcf_enabled",
            dependent_path="consent.override_vendor_purposes",
            message="Override vendor purposes cannot be enabled unless TCF mode is also enabled",
        )
    )


def _register_execution_rules() -> None:
    """Register execution-related validation rules."""

    # Custom privacy request fields in execution requires field collection enabled
    ValidationManager.register(
        PrerequisiteRule(
            name="custom_fields_execution_requires_collection",
            prerequisite_path="execution.allow_custom_privacy_request_field_collection",
            dependent_path="execution.allow_custom_privacy_request_fields_in_request_execution",
            message=(
                "allow_custom_privacy_request_fields_in_request_execution requires "
                "allow_custom_privacy_request_field_collection to be enabled"
            ),
        )
    )

    # Subject identity verification requires messaging to be configured
    # This is a cross-subsection dependency - will be validated at startup
    # when we have access to the full config and can check notification_service_type
    ValidationManager.register(
        PrerequisiteRule(
            name="subject_verification_requires_messaging",
            prerequisite_path="notifications.notification_service_type",
            dependent_path="execution.subject_identity_verification_required",
            prerequisite_value=None,  # We check that it's NOT None
            message=(
                "Subject identity verification requires a notification service to be configured. "
                "Set notifications.notification_service_type to enable verification emails/SMS."
            ),
            severity=ValidationSeverity.WARNING,
        )
    )


def _register_notification_rules() -> None:
    """Register notification-related validation rules."""

    # Send request completion notification requires notification service
    ValidationManager.register(
        RequiredSettingRule(
            name="completion_notification_requires_service",
            setting_path="notifications.notification_service_type",
            message=(
                "send_request_completion_notification is enabled but no notification "
                "service is configured. Set notifications.notification_service_type."
            ),
            condition_path="notifications.send_request_completion_notification",
            condition_value=True,
            severity=ValidationSeverity.WARNING,
        )
    )

    # Send request receipt notification requires notification service
    ValidationManager.register(
        RequiredSettingRule(
            name="receipt_notification_requires_service",
            setting_path="notifications.notification_service_type",
            message=(
                "send_request_receipt_notification is enabled but no notification "
                "service is configured. Set notifications.notification_service_type."
            ),
            condition_path="notifications.send_request_receipt_notification",
            condition_value=True,
            severity=ValidationSeverity.WARNING,
        )
    )

    # Send request review notification requires notification service
    ValidationManager.register(
        RequiredSettingRule(
            name="review_notification_requires_service",
            setting_path="notifications.notification_service_type",
            message=(
                "send_request_review_notification is enabled but no notification "
                "service is configured. Set notifications.notification_service_type."
            ),
            condition_path="notifications.send_request_review_notification",
            condition_value=True,
            severity=ValidationSeverity.WARNING,
        )
    )


def _register_security_rules() -> None:
    """Register security-related validation rules."""

    # Root username and password must both be set if either is set
    ValidationManager.register(
        ConflictRule(
            name="root_user_credentials_complete",
            setting_paths=["security.root_username", "security.root_password"],
            conflict_condition=lambda values: bool(values[0]) != bool(values[1]),
            message=(
                "Both security.root_username and security.root_password must be set "
                "if either is configured"
            ),
        )
    )

    # Parent server username and password must both be set if either is set
    ValidationManager.register(
        ConflictRule(
            name="parent_server_credentials_complete",
            setting_paths=[
                "security.parent_server_username",
                "security.parent_server_password",
            ],
            conflict_condition=lambda values: bool(values[0]) != bool(values[1]),
            message=(
                "Both security.parent_server_username and security.parent_server_password "
                "must be set if either is configured"
            ),
        )
    )

    # Bastion server fields must all be set if any is set
    ValidationManager.register(
        ConflictRule(
            name="bastion_server_config_complete",
            setting_paths=[
                "security.bastion_server_host",
                "security.bastion_server_ssh_username",
                "security.bastion_server_ssh_private_key",
            ],
            conflict_condition=lambda values: (
                # Conflict if any is set but not all are set
                any(bool(v) for v in values) and not all(bool(v) for v in values)
            ),
            message=(
                "Bastion server configuration is incomplete. All of bastion_server_host, "
                "bastion_server_ssh_username, and bastion_server_ssh_private_key must be set."
            ),
        )
    )


def _register_redis_rules() -> None:
    """Register Redis-related validation rules."""

    # Rate limiting requires Redis to be enabled
    ValidationManager.register(
        PrerequisiteRule(
            name="rate_limiting_requires_redis",
            prerequisite_path="redis.enabled",
            dependent_path="security.rate_limit_client_ip_header",
            message=(
                "Rate limiting (security.rate_limit_client_ip_header) requires Redis to be enabled. "
                "Set redis.enabled=true or remove the rate_limit_client_ip_header setting."
            ),
            severity=ValidationSeverity.WARNING,
        )
    )

    # SSL cert requirements only apply when SSL is enabled
    ValidationManager.register(
        PrerequisiteRule(
            name="redis_ssl_cert_reqs_requires_ssl",
            prerequisite_path="redis.ssl",
            dependent_path="redis.ssl_cert_reqs",
            message="redis.ssl_cert_reqs is set but redis.ssl is not enabled",
            severity=ValidationSeverity.WARNING,
        )
    )

    # Read-only Redis requires host to be set
    ValidationManager.register(
        RequiredSettingRule(
            name="redis_read_only_requires_host",
            setting_path="redis.read_only_host",
            message=(
                "redis.read_only_enabled is true but redis.read_only_host is not set"
            ),
            condition_path="redis.read_only_enabled",
            condition_value=True,
        )
    )


def _register_database_rules() -> None:
    """Register database-related validation rules."""

    # load_samples requires automigrate
    ValidationManager.register(
        PrerequisiteRule(
            name="load_samples_requires_automigrate",
            prerequisite_path="database.automigrate",
            dependent_path="database.load_samples",
            message=(
                "database.load_samples is enabled but database.automigrate is not. "
                "Sample data can only be loaded when automigrate is enabled."
            ),
        )
    )


# Register all rules when this module is imported
register_fides_rules()
