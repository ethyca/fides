from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from fides.api.models.fides_user import FidesUser
from fides.api.models.policy import ActionType, Policy, Rule
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.models.privacy_request.duplicate_group import DuplicateGroup
from fides.api.schemas.policy import DrpAction
from fides.api.schemas.privacy_request import (
    CustomPrivacyRequestField,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import Identity, LabeledIdentity
from fides.api.task.conditional_dependencies.privacy_request.privacy_request_data import (
    PrivacyRequestDataTransformer,
)
from fides.api.task.conditional_dependencies.util import transform_value_for_evaluation


@pytest.fixture
def transformer(privacy_request: PrivacyRequest):
    """Fixture to create a PrivacyRequestDataTransformer instance."""
    return PrivacyRequestDataTransformer(privacy_request)


@pytest.fixture
def test_policy(db: Session, oauth_client):
    return Policy.create(
        db=db,
        data={
            "name": "Test Policy",
            "key": "test_policy",
            "client_id": oauth_client.id,
        },
    )


@pytest.fixture
def access_rule(db: Session, test_policy: Policy, storage_config):
    Rule.create(
        db=db,
        data={
            "name": "Access Rule",
            "key": f"access_rule_{uuid4()}",
            "policy_id": test_policy.id,
            "action_type": ActionType.access,
            "storage_destination_id": storage_config.id,
        },
    )


@pytest.fixture
def erasure_rule(db: Session, test_policy: Policy):
    Rule.create(
        db=db,
        data={
            "name": "Erasure Rule",
            "key": f"erasure_rule_{uuid4()}",
            "policy_id": test_policy.id,
            "action_type": ActionType.erasure,
            "masking_strategy": {"strategy": "null_rewrite", "configuration": {}},
        },
    )


@pytest.fixture
def consent_rule(db: Session, test_policy: Policy):
    return Rule.create(
        db=db,
        data={
            "name": "Consent Rule",
            "key": f"consent_rule_{uuid4()}",
            "policy_id": test_policy.id,
            "action_type": ActionType.consent,
        },
    )


class TestPrivacyRequestToEvaluationDataBasicFields:
    """Test basic field transformation."""

    REQUIRED_FIELDS = ["id", "client_id", "status", "requested_at"]

    OPTIONAL_FIELDS = [
        "external_id",
        "source",
        "location",
        "submitted_by",
        "reviewed_by",
        "reviewed_at",
        "origin",
        "property_id",
        "duplicate_request_group_id",
    ]

    def test_basic_fields_transformed(
        self,
        transformer: PrivacyRequestDataTransformer,
        privacy_request: PrivacyRequest,
    ):
        """Test that all basic fields are correctly transformed."""
        cols = self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS
        field_addresses = [f"privacy_request.{col}" for col in cols]
        data = transformer.to_evaluation_data(field_addresses)

        for col in cols:
            assert data["privacy_request"][col] == transform_value_for_evaluation(
                getattr(privacy_request, col)
            )

    def test_optional_fields_none(self, db: Session, policy: Policy):
        """Test that optional fields are set to None when not present."""
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "policy_id": policy.id,
                "client_id": policy.client_id,
            },
        )

        cols = self.OPTIONAL_FIELDS
        field_addresses = [f"privacy_request.{col}" for col in cols]
        data = PrivacyRequestDataTransformer(privacy_request).to_evaluation_data(
            field_addresses
        )

        for col in cols:
            assert data["privacy_request"][col] is None

    def test_duplicate_request_group_id_transformed(
        self, db: Session, privacy_request: PrivacyRequest
    ):
        """Test that duplicate_request_group_id is converted to string."""

        # Create a duplicate group first (requires rule_version and dedup_key)
        duplicate_group = DuplicateGroup.create(
            db=db,
            data={
                "rule_version": "test_version_123",
                "dedup_key": "test_key",
            },
        )
        privacy_request.update(
            db=db, data={"duplicate_request_group_id": duplicate_group.id}
        )

        field_addresses = {"privacy_request.duplicate_request_group_id"}
        data = PrivacyRequestDataTransformer(privacy_request).to_evaluation_data(
            field_addresses
        )
        assert data["privacy_request"]["duplicate_request_group_id"] == str(
            duplicate_group.id
        )


class TestPrivacyRequestToEvaluationDataPolicy:
    """Test policy data transformation."""

    def test_policy_data_transformed(
        self, policy: Policy, transformer: PrivacyRequestDataTransformer
    ):
        """Test that policy data is correctly transformed."""
        cols = ["id", "key", "name", "execution_timeframe"]
        field_addresses = [f"privacy_request.policy.{col}" for col in cols]
        data = transformer.to_evaluation_data(field_addresses)

        for col in cols:
            data_col = data["privacy_request"]["policy"][col]
            assert data_col == transform_value_for_evaluation(getattr(policy, col))

    @pytest.mark.usefixtures("access_rule", "erasure_rule", "consent_rule")
    def test_policy_rules_with_all_action_types(
        self, db: Session, oauth_client, test_policy: Policy
    ):
        """Test that all policy rule action types are included."""
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "policy_id": test_policy.id,
                "client_id": oauth_client.id,
            },
        )

        cols = [
            "has_access_rule",
            "has_erasure_rule",
            "has_consent_rule",
            "has_update_rule",
            "rule_count",
            "rule_names",
            "has_storage_destination",
            "rule_action_types",
        ]
        field_addresses = [f"privacy_request.policy.{col}" for col in cols]
        data = PrivacyRequestDataTransformer(privacy_request).to_evaluation_data(
            field_addresses
        )

        assert "privacy_request" in data
        assert data["privacy_request"]["policy"]["has_access_rule"] is True
        assert data["privacy_request"]["policy"]["has_erasure_rule"] is True
        assert data["privacy_request"]["policy"]["has_consent_rule"] is True
        assert data["privacy_request"]["policy"]["has_update_rule"] is False
        assert data["privacy_request"]["policy"]["rule_count"] == 3
        assert sorted(data["privacy_request"]["policy"]["rule_names"]) == sorted(
            ["Access Rule", "Erasure Rule", "Consent Rule"]
        )
        assert sorted(data["privacy_request"]["policy"]["rule_action_types"]) == sorted(
            ["access", "erasure", "consent"]
        )
        assert data["privacy_request"]["policy"]["has_storage_destination"] is True

    def test_policy_with_no_rules(self, db: Session, oauth_client, test_policy: Policy):
        """Test policy with no rules."""
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "policy_id": test_policy.id,
                "client_id": oauth_client.id,
            },
        )

        cols = ["rule_count", "rule_action_types"]
        field_addresses = [f"privacy_request.policy.{col}" for col in cols]
        data = PrivacyRequestDataTransformer(privacy_request).to_evaluation_data(
            field_addresses
        )
        assert data["privacy_request"]["policy"]["rule_count"] == 0
        assert data["privacy_request"]["policy"]["rule_action_types"] == []

    def test_policy_drp_action_transformed(
        self, db: Session, oauth_client, test_policy: Policy
    ):
        """Test that drp_action is correctly transformed."""

        test_policy.update(db=db, data={"drp_action": DrpAction.access})

        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "policy_id": test_policy.id,
                "client_id": oauth_client.id,
            },
        )

        field_addresses = {"privacy_request.policy.drp_action"}
        data = PrivacyRequestDataTransformer(privacy_request).to_evaluation_data(
            field_addresses
        )
        assert data["privacy_request"]["policy"]["drp_action"] == "access"


class TestPrivacyRequestToEvaluationDataIdentity:
    """Test identity data transformation."""

    def test_standard_identity_fields(
        self, db: Session, privacy_request: PrivacyRequest
    ):
        """Test transformation of standard identity fields."""
        privacy_request.persist_identity(
            db=db,
            identity=Identity(
                email="user@example.com",
                phone_number="+15555555555",
                external_id="ext_123",
            ),
        )

        transformer = PrivacyRequestDataTransformer(privacy_request)
        cols = ["email", "phone_number", "external_id"]
        field_addresses = [f"privacy_request.identity.{col}" for col in cols]
        data = transformer.to_evaluation_data(field_addresses)

        for col in cols:
            assert data["privacy_request"]["identity"][
                col
            ] == transform_value_for_evaluation(
                getattr(privacy_request.get_persisted_identity(), col)
            )

    def test_custom_identity_fields(
        self,
        db: Session,
        privacy_request: PrivacyRequest,
    ):
        """Test transformation of custom identity fields with labels.

        LabeledIdentity fields should return just the value, not the full
        {"label": ..., "value": ...} structure.
        """
        field_addresses = [
            "privacy_request.identity.email",
            "privacy_request.identity.customer_id",
        ]

        # Persist custom identity fields
        privacy_request.persist_identity(
            db=db,
            identity={
                "email": "test@example.com",
                "customer_id": LabeledIdentity(label="Customer ID", value="cust_123"),
            },
        )
        transformer = PrivacyRequestDataTransformer(privacy_request)
        data = transformer.to_evaluation_data(set(field_addresses))

        # Regular identity field (email) returns the value directly
        assert data["privacy_request"]["identity"]["email"] == "test@example.com"

        # LabeledIdentity field (customer_id) should return just the value, not the full dict
        assert data["privacy_request"]["identity"]["customer_id"] == "cust_123"


class TestPrivacyRequestToEvaluationDataCustomFields:
    """Test custom privacy request fields transformation."""

    @pytest.mark.usefixtures("allow_custom_privacy_request_field_collection_enabled")
    def test_custom_privacy_request_fields(
        self,
        db: Session,
        privacy_request: PrivacyRequest,
        transformer: PrivacyRequestDataTransformer,
    ):
        """Test transformation of custom privacy request fields."""
        cols = ["legal_entity", "geolocation"]
        field_addresses = [
            f"privacy_request.custom_privacy_request_fields.{col}" for col in cols
        ]

        # No custom fields should be present
        data = transformer.to_evaluation_data(field_addresses)
        for col in cols:
            assert data["privacy_request"]["custom_privacy_request_fields"][col] is None

        # Persist custom fields
        privacy_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields={
                "legal_entity": CustomPrivacyRequestField(
                    label="Legal Entity", value="Acme Corp"
                ),
                "geolocation": CustomPrivacyRequestField(
                    label="Geolocation", value="France"
                ),
            },
        )
        transformer = PrivacyRequestDataTransformer(privacy_request)

        # Verify that the custom fields are present and return just the value (not the full dict)
        data = transformer.to_evaluation_data(field_addresses)
        assert (
            data["privacy_request"]["custom_privacy_request_fields"]["legal_entity"]
            == "Acme Corp"
        )
        assert (
            data["privacy_request"]["custom_privacy_request_fields"]["geolocation"]
            == "France"
        )

    @pytest.mark.usefixtures("allow_custom_privacy_request_field_collection_enabled")
    def test_custom_privacy_request_fields_with_array_value(
        self,
        db: Session,
        privacy_request: PrivacyRequest,
    ):
        """Test transformation of custom privacy request fields with array values."""
        field_addresses = [
            "privacy_request.custom_privacy_request_fields.data_categories"
        ]

        # Persist custom field with array value
        privacy_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields={
                "data_categories": CustomPrivacyRequestField(
                    label="Data Categories",
                    value=[
                        "User Preferences",
                        "Profile Information",
                        "Activity History",
                    ],
                ),
            },
        )
        transformer = PrivacyRequestDataTransformer(privacy_request)

        # Verify that the custom field returns just the array value, not the full dict
        data = transformer.to_evaluation_data(set(field_addresses))
        assert data["privacy_request"]["custom_privacy_request_fields"][
            "data_categories"
        ] == ["User Preferences", "Profile Information", "Activity History"]


class TestPrivacyRequestToEvaluationDataEdgeCases:
    """Test edge cases and error handling."""

    def test_none_policy(
        self, db: Session, oauth_client, privacy_request: PrivacyRequest
    ):
        """Test handling of privacy request with no policy."""
        privacy_request.update(db=db, data={"policy_id": None})

        field_addresses = {"privacy_request.policy.key"}
        transformer = PrivacyRequestDataTransformer(privacy_request)
        data = transformer.to_evaluation_data(field_addresses)
        # When policy is None, accessing policy.key returns None
        assert "privacy_request" in data
        # Since policy is None, policy.key will be None
        assert data["privacy_request"]["policy"]["key"] is None


class TestPrivacyRequestToEvaluationDataLocation:
    """Test location and location hierarchy convenience fields transformation."""

    def test_location_convenience_fields_us_state(
        self, db: Session, privacy_request: PrivacyRequest
    ):
        """Test convenience fields for US state (US-CA) - subdivision with country parent."""
        privacy_request.update(db=db, data={"location": "US-CA"})

        transformer = PrivacyRequestDataTransformer(privacy_request)
        field_addresses = {
            "privacy_request.location",
            "privacy_request.location_country",
            "privacy_request.location_groups",
            "privacy_request.location_regulations",
        }
        data = transformer.to_evaluation_data(field_addresses)

        assert data["privacy_request"]["location"] == "US-CA"
        assert data["privacy_request"]["location_country"] == "US"
        assert data["privacy_request"]["location_groups"] == ["us"]
        assert data["privacy_request"]["location_regulations"] == ["ccpa"]

    def test_location_convenience_fields_another_us_state(
        self, db: Session, privacy_request: PrivacyRequest
    ):
        """Test convenience fields for another US state (US-CO)."""
        privacy_request.update(db=db, data={"location": "US-CO"})

        transformer = PrivacyRequestDataTransformer(privacy_request)
        field_addresses = {
            "privacy_request.location_country",
            "privacy_request.location_regulations",
        }
        data = transformer.to_evaluation_data(field_addresses)

        assert data["privacy_request"]["location_country"] == "US"
        assert data["privacy_request"]["location_regulations"] == ["cpa"]

    def test_location_convenience_fields_eea_country(
        self, db: Session, privacy_request: PrivacyRequest
    ):
        """Test convenience fields for EEA country (FR) - country with regional group."""
        privacy_request.update(db=db, data={"location": "FR"})

        transformer = PrivacyRequestDataTransformer(privacy_request)
        field_addresses = {
            "privacy_request.location_country",
            "privacy_request.location_groups",
            "privacy_request.location_regulations",
        }
        data = transformer.to_evaluation_data(field_addresses)

        # France is a country itself - location_country returns the country code in uppercase
        assert data["privacy_request"]["location_country"] == "FR"
        assert data["privacy_request"]["location_groups"] == ["eea"]
        assert data["privacy_request"]["location_regulations"] == ["gdpr"]

    def test_location_convenience_fields_none_location(
        self, db: Session, privacy_request: PrivacyRequest
    ):
        """Test convenience fields when location is None."""
        privacy_request.update(db=db, data={"location": None})

        transformer = PrivacyRequestDataTransformer(privacy_request)
        field_addresses = {
            "privacy_request.location_country",
            "privacy_request.location_groups",
            "privacy_request.location_regulations",
        }
        data = transformer.to_evaluation_data(field_addresses)

        assert data["privacy_request"]["location_country"] is None
        assert data["privacy_request"]["location_groups"] == []
        assert data["privacy_request"]["location_regulations"] == []

    def test_location_convenience_fields_invalid_location(
        self, db: Session, privacy_request: PrivacyRequest
    ):
        """Test convenience fields with invalid/unknown location code."""
        privacy_request.update(db=db, data={"location": "INVALID"})

        transformer = PrivacyRequestDataTransformer(privacy_request)
        field_addresses = {"privacy_request.location_country"}
        data = transformer.to_evaluation_data(field_addresses)

        assert data["privacy_request"]["location_country"] is None

    def test_location_convenience_fields_unknown_subdivision_known_country(
        self, db: Session, privacy_request: PrivacyRequest
    ):
        """Test fallback behavior when subdivision isn't in database but country is.

        For locations like "PT-14" (Portugal region 14), the exact subdivision
        may not exist in the location database, but we can still extract and
        look up the country code "pt" to provide useful convenience fields.
        """
        # PT-14 is a subdivision format that doesn't exist in the location database,
        # but "pt" (Portugal) does
        privacy_request.update(db=db, data={"location": "PT-14"})

        transformer = PrivacyRequestDataTransformer(privacy_request)
        field_addresses = {
            "privacy_request.location_country",
            "privacy_request.location_groups",
            "privacy_request.location_regulations",
        }
        data = transformer.to_evaluation_data(field_addresses)

        # Should fall back to using the country code from the location string (uppercase)
        assert data["privacy_request"]["location_country"] == "PT"
        # Portugal belongs to the EEA
        assert data["privacy_request"]["location_groups"] == ["eea"]
        # Portugal has GDPR
        assert data["privacy_request"]["location_regulations"] == ["gdpr"]
