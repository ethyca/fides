from uuid import uuid4

import pytest
from fideslang.models import DataFlow as DataFlowSchema
from fideslang.models import PrivacyDeclaration as PrivacyDeclarationSchema
from fideslang.models import System as SystemSchema
from sqlalchemy import delete

from fides.api.db.system import create_system, update_system
from fides.api.models.sql_models import System
from fides.api.models.system_history import SystemHistory
from fides.config import get_config

CONFIG = get_config()


class TestSystemHistory:
    """Verifies the correct number of system history entries are created per system update."""

    @pytest.fixture()
    async def system(self, async_session_temp):
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name="test_system_1",
            system_type="test",
            privacy_declarations=[],
        )

        system = await create_system(
            resource, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        yield system
        delete(System).where(System.id == system.id)

    async def test_system_information_changes(
        self, db, async_session_temp, system: System
    ):
        system_schema = SystemSchema.model_validate(system)
        system_schema.description = "Test system"
        _, updated = await update_system(
            system_schema, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1
        assert system_histories[0].edited_by == CONFIG.security.root_username

    async def test_privacy_declaration_changes(
        self, db, async_session_temp, system: System
    ):
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
            system_schema, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1
        assert system_histories[0].edited_by == CONFIG.security.root_username

    async def test_ingress_egress_changes(self, db, async_session_temp, system: System):
        system_schema = SystemSchema.model_validate(system)
        system_schema.ingress = [DataFlowSchema(fides_key="upstream", type="system")]
        system_schema.egress = [DataFlowSchema(fides_key="user", type="user")]
        _, updated = await update_system(
            system_schema, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1

    async def test_multiple_changes(self, db, async_session_temp, system: System):
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
            system_schema, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 3
        for system_history in system_histories:
            assert system_history.edited_by == CONFIG.security.root_username

    async def test_no_changes(self, db, async_session_temp, system: System):
        system_schema = SystemSchema.model_validate(system)
        _, updated = await update_system(
            system_schema, async_session_temp, CONFIG.security.oauth_root_client_id
        )
        assert not updated

        assert (
            SystemHistory.filter(
                db=db, conditions=(SystemHistory.system_id == system.id)
            ).count()
            == 0
        )

    async def test_automatic_system_update(
        self, db, async_session_temp, system: System
    ):
        """If user id doesn't map to a user in the db or the root user, we just return the original user string"""
        system_schema = SystemSchema.model_validate(system)
        system_schema.description = "Test system"
        updated_system, updated = await update_system(
            system_schema, async_session_temp, "automatic_system_update"
        )
        assert updated

        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()

        assert system_histories[0].edited_by == "automatic_system_update"
