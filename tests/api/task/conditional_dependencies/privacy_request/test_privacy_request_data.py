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
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import Identity, LabeledIdentity
from fides.api.task.conditional_dependencies.privacy_request.privacy_request_data import (
    PrivacyRequestDataTransformer,
)


@pytest.fixture
def privacy_request(db: Session, policy: Policy, user: FidesUser):
    return PrivacyRequest.create(
        db=db,
        data={
            "external_id": "ext-123",
            "status": PrivacyRequestStatus.approved,
            "source": PrivacyRequestSource.privacy_center,
            "location": "US",
            "requested_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "reviewed_at": datetime(2024, 1, 2, tzinfo=timezone.utc),
            "origin": "https://example.com",
            "submitted_by": user.id,
            "property_id": "prop_123",
            "client_id": policy.client_id,
            "policy_id": policy.id,
        },
    )


@pytest.fixture
def transformer(privacy_request: PrivacyRequest):
    """Fixture to create a PrivacyRequestDataTransformer instance."""
    return PrivacyRequestDataTransformer(privacy_request)


class TestPrivacyRequestToEvaluationDataBasicFields:
    """Test basic field transformation."""

    REQUIRED_FIELDS = [
        "id",
        "client_id",
        "status",
        "requested_at",
    ]

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
            assert data["privacy_request"][col] == transformer._transform_value(
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
            assert data["privacy_request"]["policy"][
                col
            ] == transformer._transform_value(getattr(policy, col))

    def test_policy_rules_with_all_action_types(
        self, db: Session, oauth_client, storage_config
    ):
        """Test that all policy rule action types are included."""
        # Create a policy with multiple rules (access, erasure, consent)
        policy = Policy.create(
            db=db,
            data={
                "name": "Multi-rule Policy",
                "key": f"multi_rule_policy_{uuid4()}",
                "client_id": oauth_client.id,
            },
        )

        # Create access rule
        Rule.create(
            db=db,
            data={
                "name": "Access Rule",
                "key": f"access_rule_{uuid4()}",
                "policy_id": policy.id,
                "action_type": ActionType.access,
                "storage_destination_id": storage_config.id,
            },
        )

        # Create erasure rule (needs masking strategy)
        Rule.create(
            db=db,
            data={
                "name": "Erasure Rule",
                "key": f"erasure_rule_{uuid4()}",
                "policy_id": policy.id,
                "action_type": ActionType.erasure,
                "masking_strategy": {
                    "strategy": "null_rewrite",
                    "configuration": {},
                },
            },
        )

        # Create consent rule
        Rule.create(
            db=db,
            data={
                "name": "Consent Rule",
                "key": f"consent_rule_{uuid4()}",
                "policy_id": policy.id,
                "action_type": ActionType.consent,
            },
        )

        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "policy_id": policy.id,
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

    def test_policy_with_no_rules(self, db: Session, oauth_client):
        """Test policy with no rules."""
        policy = Policy.create(
            db=db,
            data={
                "name": "Empty Policy",
                "key": f"empty_policy_{uuid4()}",
                "client_id": oauth_client.id,
            },
        )

        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "policy_id": policy.id,
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

    def test_policy_drp_action_transformed(self, db: Session, oauth_client):
        """Test that drp_action is correctly transformed."""

        policy = Policy.create(
            db=db,
            data={
                "name": "DRP Policy",
                "key": f"drp_policy_{uuid4()}",
                "client_id": oauth_client.id,
                "drp_action": DrpAction.access,
            },
        )

        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "policy_id": policy.id,
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
        self,
        db: Session,
        transformer: PrivacyRequestDataTransformer,
        privacy_request: PrivacyRequest,
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

        cols = ["email", "phone_number", "external_id"]
        field_addresses = [f"privacy_request.identity.{col}" for col in cols]
        data = transformer.to_evaluation_data(field_addresses)

        for col in cols:
            assert data["privacy_request"]["identity"][
                col
            ] == transformer._transform_value(
                getattr(privacy_request.get_persisted_identity(), col)
            )

    def test_custom_identity_fields(
        self,
        db: Session,
        privacy_request: PrivacyRequest,
        transformer: PrivacyRequestDataTransformer,
    ):
        """Test transformation of custom identity fields with labels."""
        cols = ["email", "customer_id"]
        field_addresses = [f"privacy_request.identity.{col}" for col in cols]

        # No custom identity fields should be present
        data = transformer.to_evaluation_data(field_addresses)
        for col in cols:
            assert data["privacy_request"]["identity"][col] == None

        # Persist custom identity fields
        privacy_request.persist_identity(
            db=db,
            identity=Identity(
                email="user@example.com",
                customer_id=LabeledIdentity(label="Customer ID", value="cust_123"),
            ),
        )

        data = transformer.to_evaluation_data(field_addresses)

        for col in cols:
            assert data["privacy_request"]["identity"][
                col
            ] == transformer._transform_value(
                getattr(privacy_request.get_persisted_identity(), col)
            )


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
            assert data["privacy_request"]["custom_privacy_request_fields"][col] == None

        # Persist custom fields
        privacy_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields={
                "legal_entity": CustomPrivacyRequestField(
                    label="Legal Entity", value="Glamour UK"
                ),
                "geolocation": CustomPrivacyRequestField(
                    label="Geolocation", value="France"
                ),
            },
        )

        # Verify that the custom fields are present
        data = transformer.to_evaluation_data(field_addresses)
        for col in cols:
            assert data["privacy_request"]["custom_privacy_request_fields"][
                col
            ] == transformer._transform_value(
                privacy_request.get_persisted_custom_privacy_request_fields().get(col)
            )


class TestPrivacyRequestToEvaluationDataEdgeCases:
    """Test edge cases and error handling."""

    def test_none_policy(self, db: Session, oauth_client):
        """Test handling of privacy request with no policy."""
        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "status": PrivacyRequestStatus.pending,
                "client_id": oauth_client.id,
                "policy_id": None,  # Explicitly set to None
            },
        )

        field_addresses = {"privacy_request.policy.key"}
        transformer = PrivacyRequestDataTransformer(privacy_request)
        data = transformer.to_evaluation_data(field_addresses)
        # When policy is None, accessing policy.key returns None
        # The structure will have policy.key = None
        assert "privacy_request" in data
        # Since policy is None, policy.key will be None
        # The structure might be {"privacy_request": {"policy": {"key": None}}} or {"privacy_request": {"policy": None}}
        # depending on how _extract_value_by_path handles it
        if data["privacy_request"].get("policy") is not None:
            assert data["privacy_request"]["policy"].get("key") is None

    @pytest.mark.usefixtures("allow_custom_privacy_request_field_collection_enabled")
    def test_complete_data_transformation(
        self, db: Session, oauth_client, storage_config
    ):
        """Test transformation with all data types present."""
        # Create policy with multiple rules
        policy = Policy.create(
            db=db,
            data={
                "name": "Complete Policy",
                "key": f"complete_policy_{uuid4()}",
                "client_id": oauth_client.id,
                "execution_timeframe": 30,
            },
        )

        Rule.create(
            db=db,
            data={
                "name": "Access Rule",
                "key": f"access_rule_{uuid4()}",
                "policy_id": policy.id,
                "action_type": ActionType.access,
                "storage_destination_id": storage_config.id,
            },
        )

        Rule.create(
            db=db,
            data={
                "name": "Consent Rule",
                "key": f"consent_rule_{uuid4()}",
                "policy_id": policy.id,
                "action_type": ActionType.consent,
            },
        )

        privacy_request = PrivacyRequest.create(
            db=db,
            data={
                "external_id": "ext-complete",
                "status": PrivacyRequestStatus.approved,
                "source": PrivacyRequestSource.privacy_center,
                "location": "UK",
                "requested_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "policy_id": policy.id,
                "client_id": oauth_client.id,
            },
        )

        privacy_request.persist_identity(
            db=db,
            identity=Identity(
                email="user@example.com",
                customer_id=LabeledIdentity(label="Customer ID", value="cust_123"),
            ),
        )

        privacy_request.persist_custom_privacy_request_fields(
            db=db,
            custom_privacy_request_fields={
                "legal_entity": CustomPrivacyRequestField(
                    label="Legal Entity", value="Glamour UK"
                ),
            },
        )

        field_addresses = {
            "privacy_request.id",
            "privacy_request.policy.key",
            "privacy_request.identity.email",
            "privacy_request.identity.customer_id",
            "privacy_request.custom_privacy_request_fields.legal_entity",
        }
        data = PrivacyRequestDataTransformer(privacy_request).to_evaluation_data(
            field_addresses
        )

        # Verify all sections are present
        assert "privacy_request" in data
        assert "id" in data["privacy_request"]
        assert "policy" in data["privacy_request"]
        assert "identity" in data["privacy_request"]
        assert "custom_privacy_request_fields" in data["privacy_request"]

        # Verify policy data
        assert data["privacy_request"]["policy"]["key"] == policy.key

        # Verify identity data
        assert data["privacy_request"]["identity"]["email"] == "user@example.com"
        assert data["privacy_request"]["identity"]["customer_id"]["value"] == "cust_123"

        # Verify custom fields
        assert (
            data["privacy_request"]["custom_privacy_request_fields"]["legal_entity"][
                "value"
            ]
            == "Glamour UK"
        )
