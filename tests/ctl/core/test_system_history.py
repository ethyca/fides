from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fideslang.models import DataFlow as DataFlowSchema
from fideslang.models import PrivacyDeclaration as PrivacyDeclarationSchema
from fideslang.models import System as SystemSchema
from sqlalchemy import delete

from fides.api.cryptography.cryptographic_util import str_to_b64_str
from fides.api.db.system import create_system, update_system
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.sql_models import System
from fides.api.models.system_history import SystemHistory
from fides.api.oauth.roles import CONTRIBUTOR
from fides.api.schemas.user import DisabledReason
from fides.config import get_config

CONFIG = get_config()


class TestSystemHistory:
    """Verifies the correct number of system history entries are created per system update."""

    @pytest.fixture()
    async def system(self, async_session):
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name="test_system_1",
            system_type="test",
            privacy_declarations=[],
        )

        system = await create_system(
            resource, async_session, CONFIG.security.oauth_root_client_id
        )
        yield system
        delete(System).where(System.id == system.id)

    async def test_system_information_changes(self, db, async_session, system: System):
        system_schema = SystemSchema.model_validate(system)
        system_schema.description = "Test system"
        _, updated = await update_system(
            system_schema, async_session, CONFIG.security.oauth_root_client_id
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1
        assert system_histories[0].edited_by == CONFIG.security.root_username

    async def test_privacy_declaration_changes(self, db, async_session, system: System):
        system_schema = SystemSchema.model_validate(system)
        system_schema.privacy_declarations = (
            PrivacyDeclarationSchema(
                name="declaration-name",
                data_categories=[],
                data_use="essential",
                data_subjects=[],
                dataset_references=[],
            ),
        )
        _, updated = await update_system(
            system_schema, async_session, CONFIG.security.oauth_root_client_id
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1
        assert system_histories[0].edited_by == CONFIG.security.root_username

    async def test_ingress_egress_changes(self, db, async_session, system: System):
        system_schema = SystemSchema.model_validate(system)
        system_schema.ingress = [DataFlowSchema(fides_key="upstream", type="system")]
        system_schema.egress = [DataFlowSchema(fides_key="user", type="user")]
        _, updated = await update_system(
            system_schema, async_session, CONFIG.security.oauth_root_client_id
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1

    async def test_multiple_changes(self, db, async_session, system: System):
        system_schema = SystemSchema.model_validate(system)
        system_schema.description = "Test system"
        system_schema.privacy_declarations = (
            PrivacyDeclarationSchema(
                name="declaration-name",
                data_categories=[],
                data_use="essential",
                data_subjects=[],
                dataset_references=[],
            ),
        )
        system_schema.ingress = [DataFlowSchema(fides_key="upstream", type="system")]
        system_schema.egress = [DataFlowSchema(fides_key="user", type="user")]
        _, updated = await update_system(
            system_schema, async_session, CONFIG.security.oauth_root_client_id
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 3
        for system_history in system_histories:
            assert system_history.edited_by == CONFIG.security.root_username

    async def test_no_changes(self, db, async_session, system: System):
        system_schema = SystemSchema.model_validate(system)
        _, updated = await update_system(
            system_schema, async_session, CONFIG.security.oauth_root_client_id
        )
        assert not updated

        assert (
            SystemHistory.filter(
                db=db, conditions=(SystemHistory.system_id == system.id)
            ).count()
            == 0
        )

    async def test_automatic_system_update(self, db, async_session, system: System):
        """If user id doesn't map to a user in the db or the root user, we just return the original user string"""
        system_schema = SystemSchema.model_validate(system)
        system_schema.description = "Test system"
        updated_system, updated = await update_system(
            system_schema, async_session, "automatic_system_update"
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()

        assert system_histories[0].edited_by == "automatic_system_update"

    async def test_soft_deleted_user_username_still_shown_in_history(
        self, db, async_session, system: System
    ):
        """
        Verify that when a user is soft-deleted, their username is still
        shown in the system history edited_by field (not their UUID).
        """

        # Create a test user
        test_user = FidesUser.create(
            db=db,
            data={
                "username": "history_test_user",
                "password": str_to_b64_str("TESTdcnG@wzJeu0&%3Qe2fGo7"),
                "email_address": "history.test@example.com",
            },
        )
        FidesUserPermissions.create(
            db=db, data={"user_id": test_user.id, "roles": [CONTRIBUTOR]}
        )
        db.commit()

        user_id = test_user.id
        username = test_user.username

        # Update the system as this user to create a history entry
        system_schema = SystemSchema.model_validate(system)
        system_schema.description = "Updated by user who will be deleted"
        _, updated = await update_system(system_schema, async_session, user_id)
        assert updated

        # Verify the history entry shows the username
        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1
        assert system_histories[0].user_id == user_id
        assert system_histories[0].edited_by == username

        # Soft-delete the user
        test_user.deleted_at = datetime.now(timezone.utc)
        test_user.deleted_by = CONFIG.security.oauth_root_client_id
        test_user.disabled = True
        test_user.disabled_reason = DisabledReason.deleted
        db.commit()
        db.refresh(test_user)

        # Verify the user is soft-deleted
        assert test_user.is_deleted is True

        # The critical assertion: even after soft-delete, the history entry
        # should still show the username, NOT the UUID
        db.expire_all()  # Force reload from database
        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1
        assert system_histories[0].edited_by == username
