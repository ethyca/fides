from datetime import datetime, timezone
from unittest.mock import create_autospec

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.common_exceptions import FidesopsException, PrivacyRequestError
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.policy import Policy
from fides.api.models.pre_approval_webhook import PreApprovalWebhook
from fides.api.models.privacy_request import ExecutionLog
from fides.api.models.property import Property
from fides.api.models.worker_task import ExecutionLogStatus
from fides.api.oauth.roles import APPROVER
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import (
    PrivacyRequestCreate,
    PrivacyRequestSource,
    PrivacyRequestStatus,
)
from fides.api.schemas.redis_cache import Identity
from fides.config.config_proxy import ConfigProxy
from fides.service.messaging.messaging_service import MessagingService
from fides.service.privacy_request.privacy_request_service import PrivacyRequestService
from tests.conftest import wait_for_tasks_to_complete


@pytest.mark.integration
@pytest.mark.integration_postgres
class TestPrivacyRequestService:
    """
    Since these tests actually run the privacy request using the Postgres database, we need to
    mark them all as integration tests.
    """

    @pytest.fixture
    def mock_messaging_service(self) -> MessagingService:
        return create_autospec(MessagingService)

    @pytest.fixture
    def privacy_request_service(
        self, db: Session, mock_messaging_service
    ) -> PrivacyRequestService:
        return PrivacyRequestService(db, ConfigProxy(db), mock_messaging_service)

    @pytest.fixture
    def reviewing_user(self, db):
        user = FidesUser.create(
            db=db,
            data={
                "username": "reviewing_user",
                "password": "TESTdcnG@wzJeu0&%3Qe2fGo7",
                "email_address": "fides.user@ethyca.com",
            },
        )
        client = ClientDetail(
            hashed_secret="thisisatest",
            salt="thisisstillatest",
            roles=[APPROVER],
            scopes=[],
            user_id=user.id,
        )

        FidesUserPermissions.create(
            db=db, data={"user_id": user.id, "roles": [APPROVER]}
        )

        db.add(client)
        db.commit()
        db.refresh(client)
        yield user
        try:
            client.delete(db)
            user.delete(db)
        except ObjectDeletedError:
            pass

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures(
        "use_dsr_3_0",
        "postgres_integration_db",
        "automatically_approved",
        "postgres_example_test_dataset_config",
        "allow_custom_privacy_request_field_collection_enabled",
    )
    def test_resubmit_complete_privacy_request(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        mock_messaging_service: MessagingService,
        policy: Policy,
        connection_config: ConnectionConfig,
        property_a: Property,
        reviewing_user: FidesUser,
    ):
        # remove the host from the Postgres example connection
        # to force the privacy request to error
        secrets = connection_config.secrets
        host = secrets.pop("host")
        db.commit()

        external_id = "ext-123"
        requested_at = datetime.now(timezone.utc)
        identity = Identity(email="jane@example.com")
        custom_privacy_request_fields = {
            "first_name": {"label": "First name", "value": "John"}
        }
        policy_key = policy.key
        encryption_key = (
            "fake-key-1234567"  # this is not a real key, but it has to be 16 bytes
        )
        property_id = property_a.id
        source = PrivacyRequestSource.request_manager
        submitted_by = reviewing_user.id

        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                external_id=external_id,
                requested_at=requested_at,
                identity=identity,
                custom_privacy_request_fields=custom_privacy_request_fields,
                policy_key=policy_key,
                encryption_key=encryption_key,
                property_id=property_id,
                source=source,
            ),
            authenticated=True,
            submitted_by=submitted_by,
        )
        privacy_request_id = privacy_request.id

        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() > 0

        # re-add the host to fix the Postgres connection
        connection_config.secrets["host"] = host
        db.commit()

        # resubmit the request and wait for it to complete
        privacy_request = privacy_request_service.resubmit_privacy_request(
            privacy_request.id
        )
        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        db.refresh(privacy_request)

        # verify the fields from the original privacy request were copied
        # successfully to the resubmitted privacy request
        assert privacy_request.id == privacy_request_id
        assert privacy_request.status == PrivacyRequestStatus.complete
        assert privacy_request.external_id == external_id
        assert privacy_request.requested_at == requested_at
        assert privacy_request.get_persisted_identity() == identity
        assert (
            privacy_request.get_persisted_custom_privacy_request_fields()
            == custom_privacy_request_fields
        )
        assert privacy_request.policy.key == policy_key
        assert privacy_request.get_cached_encryption_key() == encryption_key
        assert privacy_request.property_id == property_id
        assert privacy_request.source == source
        assert privacy_request.submitted_by == submitted_by

        # verify the approval email was not sent out
        mock_messaging_service.send_request_approved.assert_not_called()

        # verify that the error logs from the original attempt
        # were deleted as part of the re-submission
        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() == 0

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures("automatically_approved")
    def test_cannot_resubmit_complete_privacy_request(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                identity=Identity(email="user@example.com"),
                policy_key=policy.key,
            ),
            authenticated=True,
        )

        # Manually set status to complete since there are no datasets/connections to process
        from fides.api.models.privacy_request.privacy_request import (
            PrivacyRequestStatus,
        )

        privacy_request.status = PrivacyRequestStatus.complete
        privacy_request.save(db=db)

        with pytest.raises(FidesopsException) as exc:
            privacy_request_service.resubmit_privacy_request(privacy_request.id)
        assert "Cannot resubmit a complete privacy request" in str(exc)

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures("require_manual_request_approval")
    def test_cannot_resubmit_pending_privacy_request(
        self,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                identity=Identity(email="user@example.com"),
                policy_key=policy.key,
            ),
            authenticated=True,
        )

        with pytest.raises(FidesopsException) as exc:
            privacy_request_service.resubmit_privacy_request(privacy_request.id)
        assert "Cannot resubmit a pending privacy request" in str(exc)

    def test_cannot_resubmit_non_existent_privacy_request(
        self,
        privacy_request_service: PrivacyRequestService,
    ):
        assert privacy_request_service.resubmit_privacy_request("123") is None

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures(
        "use_dsr_3_0",
        "postgres_integration_db",
        "require_manual_request_approval",
        "postgres_example_test_dataset_config",
    )
    def test_resubmit_does_not_approve_request_if_webhooks(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        mock_messaging_service: MessagingService,
        policy: Policy,
        connection_config: ConnectionConfig,
        property_a: Property,
        reviewing_user: FidesUser,
        pre_approval_webhooks: list[PreApprovalWebhook],
    ):
        """
        Test that resubmit does not automatically approve the request if require_manual_request_approval
        is True and there's PreApproval webhooks created
        """
        # remove the host from the Postgres example connection
        # to force the privacy request to error
        secrets = connection_config.secrets
        host = secrets.pop("host")

        db.commit()

        external_id = "ext-123"
        requested_at = datetime.now(timezone.utc)
        identity = Identity(email="jane@example.com")
        custom_privacy_request_fields = {
            "first_name": {"label": "First name", "value": "John"}
        }
        policy_key = policy.key
        encryption_key = (
            "fake-key-1234567"  # this is not a real key, but it has to be 16 bytes
        )
        property_id = property_a.id
        source = PrivacyRequestSource.request_manager
        submitted_by = reviewing_user.id

        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                external_id=external_id,
                requested_at=requested_at,
                identity=identity,
                custom_privacy_request_fields=custom_privacy_request_fields,
                policy_key=policy_key,
                encryption_key=encryption_key,
                property_id=property_id,
                source=source,
            ),
            authenticated=True,
            submitted_by=submitted_by,
        )
        # Manually approve it
        privacy_request_service.approve_privacy_requests(
            request_ids=[privacy_request.id], suppress_notification=True
        )
        privacy_request_id = privacy_request.id

        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        db.refresh(privacy_request)

        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() > 0

        # re-add the host to fix the Postgres connection
        connection_config.secrets["host"] = host
        db.commit()

        # resubmit the request and wait for it to complete
        privacy_request = privacy_request_service.resubmit_privacy_request(
            privacy_request.id
        )
        db.refresh(privacy_request)

        # Check that privacy request is still pending
        assert privacy_request.id == privacy_request_id
        assert privacy_request.status == PrivacyRequestStatus.pending

        # verify that the error logs from the original attempt
        # were deleted as part of the re-submission
        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() == 0

    @pytest.mark.integration
    @pytest.mark.integration_postgres
    @pytest.mark.usefixtures(
        "use_dsr_3_0",
        "postgres_integration_db",
        "require_manual_request_approval",
        "postgres_example_test_dataset_config",
        "allow_custom_privacy_request_field_collection_enabled",
    )
    def test_resubmit_automatically_approves_request_if_no_webhooks(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        mock_messaging_service: MessagingService,
        policy: Policy,
        connection_config: ConnectionConfig,
        property_a: Property,
        reviewing_user: FidesUser,
    ):
        """
        Test that resubmit does not automatically approve the request if require_manual_request_approval
        is True and there's PreApproval webhooks created
        """
        # remove the host from the Postgres example connection
        # to force the privacy request to error
        secrets = connection_config.secrets
        host = secrets.pop("host")

        db.commit()

        external_id = "ext-123"
        requested_at = datetime.now(timezone.utc)
        identity = Identity(email="jane@example.com")
        custom_privacy_request_fields = {
            "first_name": {"label": "First name", "value": "John"}
        }
        policy_key = policy.key
        encryption_key = (
            "fake-key-1234567"  # this is not a real key, but it has to be 16 bytes
        )
        property_id = property_a.id
        source = PrivacyRequestSource.request_manager
        submitted_by = reviewing_user.id

        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                external_id=external_id,
                requested_at=requested_at,
                identity=identity,
                custom_privacy_request_fields=custom_privacy_request_fields,
                policy_key=policy_key,
                encryption_key=encryption_key,
                property_id=property_id,
                source=source,
            ),
            authenticated=True,
            submitted_by=submitted_by,
        )
        # Manually approve it
        privacy_request_service.approve_privacy_requests(
            request_ids=[privacy_request.id],
            suppress_notification=True,
        )
        privacy_request_id = privacy_request.id

        wait_for_tasks_to_complete(db, privacy_request, ActionType.access)
        db.refresh(privacy_request)

        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() > 0

        # re-add the host to fix the Postgres connection
        connection_config.secrets["host"] = host
        db.commit()

        # resubmit the request and wait for it to complete
        privacy_request = privacy_request_service.resubmit_privacy_request(
            privacy_request.id
        )
        db.refresh(privacy_request)

        # Check that privacy request is complete and fields were copied properly
        assert privacy_request.id == privacy_request_id
        assert privacy_request.status == PrivacyRequestStatus.complete
        assert privacy_request.external_id == external_id
        assert privacy_request.requested_at == requested_at
        assert privacy_request.get_persisted_identity() == identity
        assert (
            privacy_request.get_persisted_custom_privacy_request_fields()
            == custom_privacy_request_fields
        )
        assert privacy_request.policy.key == policy_key
        assert privacy_request.get_cached_encryption_key() == encryption_key
        assert privacy_request.property_id == property_id
        assert privacy_request.source == source
        assert privacy_request.submitted_by == submitted_by

        # verify the approval email was not sent out
        mock_messaging_service.send_request_approved.assert_not_called()

        # verify that the error logs from the original attempt
        # were deleted as part of the re-submission
        error_logs = privacy_request.execution_logs.filter(
            ExecutionLog.status == ExecutionLogStatus.error
        )
        assert error_logs.count() == 0

    @pytest.mark.integration
    def test_create_privacy_request_with_masking_secrets(
        self,
        privacy_request_service: PrivacyRequestService,
        erasure_policy_aes: Policy,
    ):
        """
        Test that a privacy request with a policy that needs masking secrets
        persists the masking secrets to the database.
        """
        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                identity=Identity(email="user@example.com"),
                policy_key=erasure_policy_aes.key,
            ),
            authenticated=True,
        )
        assert privacy_request.masking_secrets is not None
        assert len(privacy_request.masking_secrets) > 0

    def test_create_privacy_request_location_required_but_missing(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that a PrivacyRequestError is raised when a location field is required but location is not provided"""
        from fides.api.common_exceptions import PrivacyRequestError
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Create Privacy Center configuration with a required location field for this policy
        privacy_center_config_data = {
            "config": {
                "title": "Test Privacy Center",
                "description": "Test privacy center for location validation",
                "actions": [
                    {
                        "policy_key": policy.key,
                        "title": "Test Action",
                        "description": "Test action for location validation",
                        "icon_path": "/test-icon.svg",
                        "identity_inputs": {"email": "required"},
                        "custom_privacy_request_fields": {
                            "location": {
                                "label": "Your Location",
                                "field_type": "location",
                                "required": True,
                                "ip_geolocation_hint": False,
                            }
                        },
                    }
                ],
                "consent": {
                    "button": {
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "icon_path": "/consent.svg",
                        "identity_inputs": {"email": "optional"},
                        "title": "Manage preferences",
                        "modalTitle": "Manage your consent preferences",
                        "confirmButtonText": "Continue",
                        "cancelButtonText": "Cancel",
                    },
                    "page": {
                        "consentOptions": [],
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "policy_key": "default_consent_policy",
                        "title": "Manage your consent",
                    },
                },
            }
        }

        privacy_center_config = PrivacyCenterConfig.create_or_update(
            db=db, data=privacy_center_config_data
        )

        identity = Identity(email="jane@example.com")

        try:
            with pytest.raises(PrivacyRequestError) as exc_info:
                privacy_request_service.create_privacy_request(
                    PrivacyRequestCreate(
                        identity=identity,
                        policy_key=policy.key,
                        # location is missing here intentionally
                    ),
                    authenticated=True,
                )

            assert (
                "Location is required for field 'location' but was not provided"
                in str(exc_info.value)
            )
        finally:
            # Cleanup
            privacy_center_config.delete(db)

    def test_create_privacy_request_location_required_property_config_used_when_provided(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
        property_a: Property,
    ):
        """Property config takes precedence: required location enforced when property_id provided."""
        from fides.api.common_exceptions import PrivacyRequestError
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Global config without location requirement
        global_config = PrivacyCenterConfig.create_or_update(
            db=db,
            data={
                "config": {
                    "title": "Global",
                    "description": "Global config",
                    "actions": [
                        {
                            "policy_key": policy.key,
                            "title": "Action",
                            "description": "desc",
                            "icon_path": "/icon.svg",
                            "identity_inputs": {"email": "required"},
                        }
                    ],
                    "consent": {
                        "button": {
                            "description": "desc",
                            "description_subtext": [],
                            "icon_path": "/consent.svg",
                            "identity_inputs": {"email": "optional"},
                            "title": "Manage",
                            "modalTitle": "Manage",
                            "confirmButtonText": "Continue",
                            "cancelButtonText": "Cancel",
                        },
                        "page": {
                            "consentOptions": [],
                            "description": "desc",
                            "description_subtext": [],
                            "policy_key": "default_consent_policy",
                            "title": "Manage",
                        },
                    },
                }
            },
        )

        # Set property config requiring location
        property_a.update(
            db=db,
            data={
                "privacy_center_config": {
                    "title": "Property",
                    "description": "Property config",
                    "actions": [
                        {
                            "policy_key": policy.key,
                            "title": "Action",
                            "description": "desc",
                            "icon_path": "/icon.svg",
                            "identity_inputs": {"email": "required"},
                            "custom_privacy_request_fields": {
                                "location": {
                                    "label": "Location",
                                    "field_type": "location",
                                    "required": True,
                                    "ip_geolocation_hint": False,
                                }
                            },
                        }
                    ],
                    "consent": {
                        "button": {
                            "description": "desc",
                            "description_subtext": [],
                            "icon_path": "/consent.svg",
                            "identity_inputs": {"email": "optional"},
                            "title": "Manage",
                            "modalTitle": "Manage",
                            "confirmButtonText": "Continue",
                            "cancelButtonText": "Cancel",
                        },
                        "page": {
                            "consentOptions": [],
                            "description": "desc",
                            "description_subtext": [],
                            "policy_key": "default_consent_policy",
                            "title": "Manage",
                        },
                    },
                }
            },
        )

        identity = Identity(email="jane@example.com")

        try:
            with pytest.raises(PrivacyRequestError):
                privacy_request_service.create_privacy_request(
                    PrivacyRequestCreate(
                        identity=identity,
                        policy_key=policy.key,
                        property_id=property_a.id,  # property config should be used
                    ),
                    authenticated=True,
                )
        finally:
            global_config.delete(db)

    def test_create_privacy_request_location_required_default_property_config_when_no_property_id(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
        property_a: Property,
    ):
        """Default property config used when no property_id provided."""
        # Make property_a default and set required location on its config
        property_a.update(
            db=db,
            data={
                "is_default": True,
                "privacy_center_config": {
                    "title": "Default Property",
                    "description": "Default property config",
                    "actions": [
                        {
                            "policy_key": policy.key,
                            "title": "Action",
                            "description": "desc",
                            "icon_path": "/icon.svg",
                            "identity_inputs": {"email": "required"},
                            "custom_privacy_request_fields": {
                                "location": {
                                    "label": "Location",
                                    "field_type": "location",
                                    "required": True,
                                    "ip_geolocation_hint": False,
                                }
                            },
                        }
                    ],
                    "consent": {
                        "button": {
                            "description": "desc",
                            "description_subtext": [],
                            "icon_path": "/consent.svg",
                            "identity_inputs": {"email": "optional"},
                            "title": "Manage",
                            "modalTitle": "Manage",
                            "confirmButtonText": "Continue",
                            "cancelButtonText": "Cancel",
                        },
                        "page": {
                            "consentOptions": [],
                            "description": "desc",
                            "description_subtext": [],
                            "policy_key": "default_consent_policy",
                            "title": "Manage",
                        },
                    },
                },
            },
        )

        identity = Identity(email="jane@example.com")

        with pytest.raises(PrivacyRequestError):
            privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    identity=identity,
                    policy_key=policy.key,
                    # no property_id -> should use default property's config
                ),
                authenticated=True,
            )

    def test_create_privacy_request_location_required_falls_back_to_global_when_no_property_configs(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Global single-row config used when no property configs available."""
        from fides.api.common_exceptions import PrivacyRequestError
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Ensure no default property present with config
        # Create global config requiring location
        global_config = PrivacyCenterConfig.create_or_update(
            db=db,
            data={
                "config": {
                    "title": "Global Required",
                    "description": "Global requires location",
                    "actions": [
                        {
                            "policy_key": policy.key,
                            "title": "Action",
                            "description": "desc",
                            "icon_path": "/icon.svg",
                            "identity_inputs": {"email": "required"},
                            "custom_privacy_request_fields": {
                                "location": {
                                    "label": "Location",
                                    "field_type": "location",
                                    "required": True,
                                    "ip_geolocation_hint": False,
                                }
                            },
                        }
                    ],
                    "consent": {
                        "button": {
                            "description": "desc",
                            "description_subtext": [],
                            "icon_path": "/consent.svg",
                            "identity_inputs": {"email": "optional"},
                            "title": "Manage",
                            "modalTitle": "Manage",
                            "confirmButtonText": "Continue",
                            "cancelButtonText": "Cancel",
                        },
                        "page": {
                            "consentOptions": [],
                            "description": "desc",
                            "description_subtext": [],
                            "policy_key": "default_consent_policy",
                            "title": "Manage",
                        },
                    },
                }
            },
        )

        identity = Identity(email="jane@example.com")

        try:
            with pytest.raises(PrivacyRequestError):
                privacy_request_service.create_privacy_request(
                    PrivacyRequestCreate(
                        identity=identity,
                        policy_key=policy.key,
                    ),
                    authenticated=True,
                )
        finally:
            global_config.delete(db)
    def test_create_privacy_request_location_required_and_provided(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that privacy request creation succeeds when required location is provided"""
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Create Privacy Center configuration with a required location field for this policy
        privacy_center_config_data = {
            "config": {
                "title": "Test Privacy Center",
                "description": "Test privacy center for location validation",
                "actions": [
                    {
                        "policy_key": policy.key,
                        "title": "Test Action",
                        "description": "Test action for location validation",
                        "icon_path": "/test-icon.svg",
                        "identity_inputs": {"email": "required"},
                        "custom_privacy_request_fields": {
                            "location": {
                                "label": "Your Location",
                                "field_type": "location",
                                "required": True,
                                "ip_geolocation_hint": False,
                            }
                        },
                    }
                ],
                "consent": {
                    "button": {
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "icon_path": "/consent.svg",
                        "identity_inputs": {"email": "optional"},
                        "title": "Manage preferences",
                        "modalTitle": "Manage your consent preferences",
                        "confirmButtonText": "Continue",
                        "cancelButtonText": "Cancel",
                    },
                    "page": {
                        "consentOptions": [],
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "policy_key": "default_consent_policy",
                        "title": "Manage your consent",
                    },
                },
            }
        }

        privacy_center_config = PrivacyCenterConfig.create_or_update(
            db=db, data=privacy_center_config_data
        )

        identity = Identity(email="jane@example.com")

        try:
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    identity=identity,
                    policy_key=policy.key,
                    location="US-CA",  # location provided
                ),
                authenticated=True,
            )

            assert privacy_request.location == "US-CA"
            assert privacy_request.status == PrivacyRequestStatus.pending
        finally:
            # Cleanup
            privacy_center_config.delete(db)

    def test_create_privacy_request_location_validation_no_config(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that validation is skipped when no Privacy Center config exists"""
        # Ensure no Privacy Center config exists
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        PrivacyCenterConfig.delete_all(db)
        db.commit()

        identity = Identity(email="jane@example.com")

        # Should not raise an error, validation is skipped
        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                identity=identity,
                policy_key=policy.key,
                # No location provided, but validation skipped due to no config
            ),
            authenticated=True,
        )

        assert privacy_request.location is None
        assert privacy_request.status == PrivacyRequestStatus.pending

    def test_create_privacy_request_location_validation_invalid_config(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that validation is skipped when Privacy Center config fails to parse"""
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Create an invalid Privacy Center config that will fail parsing
        invalid_config_data = {
            "config": {
                # Missing required fields like 'title', 'description', 'consent'
                "actions": [
                    {
                        "policy_key": policy.key,
                        # Missing required fields like 'title', 'description'
                        "custom_privacy_request_fields": {
                            "location": {
                                "field_type": "location",
                                "required": True,
                            }
                        },
                    }
                ]
            }
        }

        privacy_center_config = PrivacyCenterConfig.create_or_update(
            db=db, data=invalid_config_data
        )

        identity = Identity(email="jane@example.com")

        try:
            # Should not raise an error, validation is skipped due to parse failure
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    identity=identity,
                    policy_key=policy.key,
                    # No location provided, but validation skipped due to config parse error
                ),
                authenticated=True,
            )

            assert privacy_request.location is None
            assert privacy_request.status == PrivacyRequestStatus.pending
        finally:
            privacy_center_config.delete(db)

    def test_create_privacy_request_location_validation_no_matching_action(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that validation is skipped when no action matches the policy key"""
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Create Privacy Center config with action for a different policy
        privacy_center_config_data = {
            "config": {
                "title": "Test Privacy Center",
                "description": "Test privacy center for location validation",
                "actions": [
                    {
                        "policy_key": "different_policy_key",  # Different policy key
                        "title": "Different Action",
                        "description": "Action for different policy",
                        "icon_path": "/test-icon.svg",
                        "identity_inputs": {"email": "required"},
                        "custom_privacy_request_fields": {
                            "location": {
                                "label": "Your Location",
                                "field_type": "location",
                                "required": True,
                                "ip_geolocation_hint": False,
                            }
                        },
                    }
                ],
                "consent": {
                    "button": {
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "icon_path": "/consent.svg",
                        "identity_inputs": {"email": "optional"},
                        "title": "Manage preferences",
                        "modalTitle": "Manage your consent preferences",
                        "confirmButtonText": "Continue",
                        "cancelButtonText": "Cancel",
                    },
                    "page": {
                        "consentOptions": [],
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "policy_key": "default_consent_policy",
                        "title": "Manage your consent",
                    },
                },
            }
        }

        privacy_center_config = PrivacyCenterConfig.create_or_update(
            db=db, data=privacy_center_config_data
        )

        identity = Identity(email="jane@example.com")

        try:
            # Should not raise an error, validation is skipped due to no matching action
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    identity=identity,
                    policy_key=policy.key,  # Uses the test policy, not the one in config
                    # No location provided, but validation skipped due to no matching action
                ),
                authenticated=True,
            )

            assert privacy_request.location is None
            assert privacy_request.status == PrivacyRequestStatus.pending
        finally:
            privacy_center_config.delete(db)

    def test_create_privacy_request_location_validation_no_custom_fields(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that validation is skipped when action has no custom_privacy_request_fields"""
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Create Privacy Center config with action that has no custom fields
        privacy_center_config_data = {
            "config": {
                "title": "Test Privacy Center",
                "description": "Test privacy center for location validation",
                "actions": [
                    {
                        "policy_key": policy.key,
                        "title": "Test Action",
                        "description": "Test action for location validation",
                        "icon_path": "/test-icon.svg",
                        "identity_inputs": {"email": "required"},
                        # No custom_privacy_request_fields defined
                    }
                ],
                "consent": {
                    "button": {
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "icon_path": "/consent.svg",
                        "identity_inputs": {"email": "optional"},
                        "title": "Manage preferences",
                        "modalTitle": "Manage your consent preferences",
                        "confirmButtonText": "Continue",
                        "cancelButtonText": "Cancel",
                    },
                    "page": {
                        "consentOptions": [],
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "policy_key": "default_consent_policy",
                        "title": "Manage your consent",
                    },
                },
            }
        }

        privacy_center_config = PrivacyCenterConfig.create_or_update(
            db=db, data=privacy_center_config_data
        )

        identity = Identity(email="jane@example.com")

        try:
            # Should not raise an error, validation is skipped due to no custom fields
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    identity=identity,
                    policy_key=policy.key,
                    # No location provided, but validation skipped due to no custom fields
                ),
                authenticated=True,
            )

            assert privacy_request.location is None
            assert privacy_request.status == PrivacyRequestStatus.pending
        finally:
            privacy_center_config.delete(db)

    def test_create_privacy_request_location_field_not_required(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that validation passes when location field exists but is not required"""
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Create Privacy Center config with optional location field
        privacy_center_config_data = {
            "config": {
                "title": "Test Privacy Center",
                "description": "Test privacy center for location validation",
                "actions": [
                    {
                        "policy_key": policy.key,
                        "title": "Test Action",
                        "description": "Test action for location validation",
                        "icon_path": "/test-icon.svg",
                        "identity_inputs": {"email": "required"},
                        "custom_privacy_request_fields": {
                            "location": {
                                "label": "Your Location",
                                "field_type": "location",
                                "required": False,  # Not required
                                "ip_geolocation_hint": False,
                            }
                        },
                    }
                ],
                "consent": {
                    "button": {
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "icon_path": "/consent.svg",
                        "identity_inputs": {"email": "optional"},
                        "title": "Manage preferences",
                        "modalTitle": "Manage your consent preferences",
                        "confirmButtonText": "Continue",
                        "cancelButtonText": "Cancel",
                    },
                    "page": {
                        "consentOptions": [],
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "policy_key": "default_consent_policy",
                        "title": "Manage your consent",
                    },
                },
            }
        }

        privacy_center_config = PrivacyCenterConfig.create_or_update(
            db=db, data=privacy_center_config_data
        )

        identity = Identity(email="jane@example.com")

        try:
            # Should not raise an error, location field is not required
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    identity=identity,
                    policy_key=policy.key,
                    # No location provided, but field is not required
                ),
                authenticated=True,
            )

            assert privacy_request.location is None
            assert privacy_request.status == PrivacyRequestStatus.pending
        finally:
            privacy_center_config.delete(db)

    def test_create_privacy_request_location_required_field_has_value_in_request_data(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that validation passes when required location field has value in custom_privacy_request_fields"""
        from fides.api.common_exceptions import PrivacyRequestError
        from fides.api.models.privacy_center_config import PrivacyCenterConfig

        # Create Privacy Center config with required location field
        privacy_center_config_data = {
            "config": {
                "title": "Test Privacy Center",
                "description": "Test privacy center for location validation",
                "actions": [
                    {
                        "policy_key": policy.key,
                        "title": "Test Action",
                        "description": "Test action for location validation",
                        "icon_path": "/test-icon.svg",
                        "identity_inputs": {"email": "required"},
                        "custom_privacy_request_fields": {
                            "location": {
                                "label": "Your Location",
                                "field_type": "location",
                                "required": True,
                                "ip_geolocation_hint": False,
                            }
                        },
                    }
                ],
                "consent": {
                    "button": {
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "icon_path": "/consent.svg",
                        "identity_inputs": {"email": "optional"},
                        "title": "Manage preferences",
                        "modalTitle": "Manage your consent preferences",
                        "confirmButtonText": "Continue",
                        "cancelButtonText": "Cancel",
                    },
                    "page": {
                        "consentOptions": [],
                        "description": "Manage your consent preferences",
                        "description_subtext": [],
                        "policy_key": "default_consent_policy",
                        "title": "Manage your consent",
                    },
                },
            }
        }

        privacy_center_config = PrivacyCenterConfig.create_or_update(
            db=db, data=privacy_center_config_data
        )

        identity = Identity(email="jane@example.com")

        try:
            # Should not raise an error, location field has value in custom fields
            privacy_request = privacy_request_service.create_privacy_request(
                PrivacyRequestCreate(
                    identity=identity,
                    policy_key=policy.key,
                    custom_privacy_request_fields={
                        "location": {
                            "label": "Your Location",
                            "value": "US-CA",
                        }  # Location provided in custom fields
                    },
                    # No location parameter, but field has value in custom_privacy_request_fields
                ),
                authenticated=True,
            )

            assert (
                privacy_request.location is None
            )  # Location parameter wasn't provided
            assert privacy_request.status == PrivacyRequestStatus.pending
        finally:
            privacy_center_config.delete(db)

    def test_create_privacy_request_location_optional_and_missing(
        self,
        db: Session,
        privacy_request_service: PrivacyRequestService,
        policy: Policy,
    ):
        """Test that privacy request creation succeeds when location field is optional and not provided"""
        identity = Identity(email="jane@example.com")
        custom_privacy_request_fields = {
            "optional_field": {
                "label": "Optional Field",
                "value": "",
            }  # Optional field (no "location" in name)
        }

        privacy_request = privacy_request_service.create_privacy_request(
            PrivacyRequestCreate(
                identity=identity,
                custom_privacy_request_fields=custom_privacy_request_fields,
                policy_key=policy.key,
                # location is missing but field is optional
            ),
            authenticated=True,
        )

        assert privacy_request.location is None
        assert privacy_request.status == PrivacyRequestStatus.pending
