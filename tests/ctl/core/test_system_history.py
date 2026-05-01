import logging
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fideslang.models import DataFlow as DataFlowSchema
from fideslang.models import PrivacyDeclaration as PrivacyDeclarationSchema
from fideslang.models import System as SystemSchema
from sqlalchemy import delete

from fides.api.db.crud import get_resource
from fides.api.db.system import create_system, update_system, upsert_system
from fides.api.models.sql_models import System
from fides.api.models.system_history import SystemHistory
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


class TestUpsertSystemFetchOptimization:
    """Regression coverage for the ENG-3593 fetch-count reduction in
    /system/upsert. Each updated system used to fan out to 4 get_resource
    calls; after the fix it should be exactly 1."""

    @pytest.fixture()
    async def system(self, async_session):
        resource = SystemSchema(
            fides_key=str(uuid4()),
            organization_fides_key="default_organization",
            name="upsert_fetch_opt_system",
            system_type="test",
            privacy_declarations=[],
        )

        system = await create_system(
            resource, async_session, CONFIG.security.oauth_root_client_id
        )
        yield system
        delete(System).where(System.id == system.id)

    async def test_upsert_passes_existing_system_to_update(
        self, async_session, system: System
    ):
        """upsert_system must pass the System loaded by its existence check
        through to update_system as `existing_system`. If this contract is
        broken, the redundant fetch the optimization removed is silently
        re-introduced via update_system's fallback path."""
        system_schema = SystemSchema.model_validate(system)

        with patch(
            "fides.api.db.system.update_system",
            new=AsyncMock(return_value=(system, False)),
        ) as mock_update:
            await upsert_system(
                resources=[system_schema],
                db=async_session,
                current_user_id=CONFIG.security.oauth_root_client_id,
            )

        mock_update.assert_called_once()
        call_kwargs = mock_update.call_args.kwargs
        assert call_kwargs.get("existing_system") is not None, (
            "update_system was called without existing_system - this defeats "
            "the ENG-3593 fetch optimization."
        )
        assert call_kwargs["existing_system"].fides_key == system.fides_key

    async def test_update_system_with_existing_system_persists_changes(
        self, db, async_session, system: System
    ):
        """When update_system is called with an explicit existing_system
        (the new ENG-3593 code path), the inline UPDATE + db.refresh still
        persist the change to the DB and emit the expected audit entry."""
        pre_loaded = await get_resource(System, system.fides_key, async_session)

        system_schema = SystemSchema.model_validate(system)
        system_schema.description = "Modified via explicit existing_system path"

        _, updated = await update_system(
            resource=system_schema,
            db=async_session,
            current_user_id=CONFIG.security.oauth_root_client_id,
            existing_system=pre_loaded,
        )
        assert updated

        # The DB row was actually updated.
        fresh = await get_resource(System, system.fides_key, async_session)
        assert fresh.description == "Modified via explicit existing_system path"

        # An audit entry on the general axis was created.
        system_histories = SystemHistory.filter(
            db=db, conditions=(SystemHistory.system_id == system.id)
        ).all()
        assert len(system_histories) == 1

    async def test_upsert_system_emits_one_fetch_per_updated_system(
        self, async_session, loguru_caplog
    ):
        """Regression guard for ENG-3593: each updated system on the UPDATE
        path should emit exactly one 'Fetching resource' debug log for its
        fides_key. Before the fix this was four. If a future change re-
        introduces a redundant get_resource call, this test fails loudly.

        Uses two systems to also catch any accidental constant-cost bug
        (e.g., loading systems once but counting wrong).
        """
        loguru_caplog.set_level(logging.DEBUG)

        payload = [
            SystemSchema(
                fides_key=f"fetch_count_{uuid4()}",
                organization_fides_key="default_organization",
                name=f"Fetch count test {i}",
                system_type="test",
                privacy_declarations=[],
            )
            for i in range(2)
        ]

        # Prime: this run creates the rows (INSERT path); not what we measure.
        await upsert_system(
            resources=payload,
            db=async_session,
            current_user_id=CONFIG.security.oauth_root_client_id,
        )

        # Drop log lines from the prime so the count below reflects only the
        # measure pass.
        loguru_caplog.clear()

        # Measure: every row exists, every row hits the UPDATE path.
        await upsert_system(
            resources=payload,
            db=async_session,
            current_user_id=CONFIG.security.oauth_root_client_id,
        )

        for resource in payload:
            matching = [
                line
                for line in loguru_caplog.text.splitlines()
                if "Fetching resource" in line and resource.fides_key in line
            ]
            assert len(matching) == 1, (
                f"Expected exactly 1 'Fetching resource' log for "
                f"{resource.fides_key} on the UPDATE path, found "
                f"{len(matching)}:\n" + "\n".join(matching)
            )
