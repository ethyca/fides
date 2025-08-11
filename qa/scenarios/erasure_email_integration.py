#!/usr/bin/env python3
"""
QA scenario for testing generic erasure email integration.
"""

from typing import Dict, Any

from utils import QATestScenario, Argument


class ErasureEmailIntegration(QATestScenario):
    """QA scenario for testing generic erasure email integration."""

    arguments = {
        "email": Argument(
            type=str,
            default=None,
            description="Email address to use for both test and recipient emails (required)",
        )
    }

    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
        self.system_name = "qa_erasure_email_system"
        self.connection_key = "qa_erasure_email_connection"
        self.third_party_vendor_name = "Test Vendor Name"

        # Store email argument
        self.email_address = kwargs.get("email")

        # Validate required email argument
        if not self.email_address:
            raise ValueError(
                "Email address is required. Use --email your.email@example.com"
            )

    @property
    def description(self) -> str:
        return "Creates a system with generic erasure email integration for testing erasure email workflows."

    def setup(self) -> bool:
        """Setup erasure email integration."""
        self.setup_phase()

        try:
            # Step 1: Validate email configuration
            self.step(1, "Validating email configuration")
            self._validate_email_config()

            # Step 2: Create the system
            self.step(2, "Creating erasure email system")
            self._create_system()

            # Step 3: Create the erasure email connection
            self.step(3, "Creating erasure email connection")
            self._create_erasure_email_connection()

            self.final_success(
                f"Erasure email integration setup complete! Test emails will be sent to {self.email_address}"
            )
            return True

        except Exception as e:
            self.final_error(f"Setup failed: {e}")
            return False

    def teardown(self) -> bool:
        """Clean up all resources created by this scenario."""
        self.cleanup_phase()

        success = True
        deleted_counts = {"connections": 0, "systems": 0}

        try:
            # Step 1: Delete connection FIRST (no datasets to link in email connectors)
            self.step(1, "Deleting erasure email connection")
            if self.api.delete_connection(self.connection_key):
                deleted_counts["connections"] += 1
                self.success(f"Deleted connection: {self.connection_key}")
            else:
                self.already_cleaned("Connection", self.connection_key)

            # Step 2: Delete system
            self.step(2, "Deleting erasure email system")
            if self.api.delete_system(self.system_name):
                deleted_counts["systems"] += 1
                self.success(f"Deleted system: {self.system_name}")
            else:
                self.already_cleaned("System", self.system_name)

            # Note about email workflow
            self.info(
                "Note: Erasure email integration removed - no external data affected"
            )

            # Show results
            self.summary("Cleanup Summary", deleted_counts)

            return success

        except Exception as e:
            self.final_error(f"Teardown failed: {e}")
            return False

    def _validate_email_config(self) -> None:
        """Validate the email configuration."""
        # Basic email validation (pydantic EmailStr would be better, but this is a simple check)
        if "@" not in self.email_address or "." not in self.email_address:
            raise ValueError(f"Invalid email address format: {self.email_address}")

        self.success("Email configuration validated successfully")
        self.success(f"Test email address: {self.email_address}")
        self.success(f"Recipient email address: {self.email_address}")
        self.success(f"Third-party vendor name: {self.third_party_vendor_name}")

    def _create_system(self) -> bool:
        """Create the erasure email system."""
        try:
            system_data = {
                "fides_key": self.system_name,
                "organization_fides_key": "default_organization",
                "name": "QA Erasure Email System",
                "description": "Test system for erasure email integration testing.",
                "system_type": "Service",
                "privacy_declarations": [],
                "system_dependencies": [],
            }
            self.api.create_system(system_data)
            self.success("Erasure email system created successfully")
            return True
        except Exception as e:
            self.error(f"Failed to create system: {e}")
            raise

    def _create_erasure_email_connection(self) -> bool:
        """Create erasure email connection linked to system."""
        try:
            # Configure the email connection secrets according to EmailSchema
            secrets = {
                "test_email_address": self.email_address,
                "recipient_email_address": self.email_address,
                "third_party_vendor_name": self.third_party_vendor_name,
                "advanced_settings": {
                    "identity_types": {"email": True, "phone_number": False}
                },
            }

            connection_data = {
                "name": "QA Erasure Email Connection",
                "key": self.connection_key,
                "connection_type": "generic_erasure_email",
                "access": "write",
                "description": "Test erasure email connection for privacy request erasure workflows",
                "secrets": secrets,
            }

            self.api.create_system_connection(self.system_name, connection_data)
            self.success("Erasure email connection created and linked successfully")
            self.info(
                f"Connection configured for vendor: {self.third_party_vendor_name}"
            )
            return True
        except Exception as e:
            self.error(f"Failed to create erasure email connection: {e}")
            raise
