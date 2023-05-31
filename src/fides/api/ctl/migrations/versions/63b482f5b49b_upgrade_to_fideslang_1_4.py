"""Upgrade to fideslang 1.4

Revision ID: 63b482f5b49b
Revises: 2661f31daffb
Create Date: 2023-05-26 07:51:25.947974

"""
import asyncio
from typing import Dict

from fides.api.ctl.database.crud import list_resource, upsert_resources
from fides.api.ctl.database.session import async_session
from fides.api.ctl.sql_models import PolicyCtl, PrivacyDeclaration
from fides.api.models.privacy_notice import PrivacyNotice, PrivacyNoticeHistory
from fides.api.models.privacy_request import Consent

# revision identifiers, used by Alembic.
revision = "63b482f5b49b"
down_revision = "2661f31daffb"
branch_labels = None
depends_on = None

# The `key` is the old value, the `value` is the new value
data_use_upgrades: Dict[str, str] = {
    "third_party_sharing.payment_processing": "essential.service.payment_processing"
    "third_party_sharing.fraud_detection",
    "essential.service.fraud_detection"
    "advertising.first_party": "marketing.advertising.first_party",
    "advertising.first_party.contextual": "marketing.advertising.first_party.contextual",
    "advertising.first_party.personalized": "marketing.advertising.first_party.targeted",
    "advertising.third_party": "marketing.advertising.third_party.targeted",
    "advertising.third_party.personalized": "marketing.advertising.third_party.targeted",
    "third_party_sharing.personalized_advertising": "marketing.advertising.third_party.targeted",
    "provide": "essential",
    "provide.service": "essential.service",
}
data_use_downgrades: Dict[str, str] = {
    value: key for key, value in data_use_upgrades.items()
}


async def upgrade_privacy_declarations() -> None:
    async with async_session() as session:
        resources = await list_resource(PrivacyDeclaration, session)

        for resource in resources:
            current_data_use = resource.data_use

            if current_data_use in data_use_upgrades.keys():
                resource.data_use = data_use_upgrades[resource.data_use]

        await upsert_resources(PrivacyDeclaration, resources, session)

        # Since we can't write tests for data migrations, we do it live
        existing_resources = await list_resource(PrivacyDeclaration, session)
        assert not any(
            [
                resource.data_use in data_use_upgrades.keys()
                for resource in existing_resources
            ]
        ), "ERROR: Data Use Upgrade for Fideslang v1.4 failed for Privacy Declarations!"


async def upgrade_policy_rules() -> None:
    async with async_session() as session:
        resources = await list_resource(PolicyCtl, session)
        for resource in resources:
            for rule in resource.rules:
                current_data_use = rule.data_use
                if current_data_use in data_use_upgrades.keys():
                    rule.data_use = data_use_upgrades[resource.data_use]
        await upsert_resources(PolicyCtl, resources, session)

        # Since we can't write tests for data migrations, we do it live
        existing_resources = await list_resource(PolicyCtl, session)
        assert not any(
            [
                rule.data_use in data_use_upgrades.keys()
                for resource in existing_resources
                for rule in resource
            ]
        ), "ERROR: Data Use Upgrade for Fideslang v1.4 failed for Policy Rules!"


def upgrade() -> None:
    "Update every place that refers to data uses."
    loop = asyncio.get_running_loop()
    asyncio.ensure_future(upgrade_privacy_declarations(), loop=loop)
    asyncio.ensure_future(upgrade_policy_rules(), loop=loop)


async def downgrade_privacy_declarations() -> None:
    async with async_session() as session:
        resources = await list_resource(PrivacyDeclaration, session)

        for resource in resources:
            current_data_use = resource.data_use

            if current_data_use in data_use_downgrades.values():
                resource.data_use = data_use_downgrades[resource.data_use]

        await upsert_resources(PrivacyDeclaration, resources, session)

        # Since we can't write tests for data migrations, we do it live
        existing_resources = await list_resource(PrivacyDeclaration, session)
        assert not any(
            [
                resource.data_use in data_use_downgrades.keys()
                for resource in existing_resources
            ]
        ), "ERROR: Data Use Downgrade for Fideslang v1.4 failed for Privacy Declarations!"


async def downgrade_policy_rules() -> None:
    async with async_session() as session:
        resources = await list_resource(PolicyCtl, session)
        for resource in resources:
            for rule in resource.rules:
                current_data_use = rule.data_use
                if current_data_use in data_use_downgrades.keys():
                    rule.data_use = data_use_downgrades[resource.data_use]
        await upsert_resources(PolicyCtl, resources, session)

        # Since we can't write tests for data migrations, we do it live
        existing_resources = await list_resource(PolicyCtl, session)
        assert not any(
            [
                rule.data_use in data_use_downgrades.keys()
                for resource in existing_resources
                for rule in resource
            ]
        ), "ERROR: Data Use Downgrade from Fideslang v1.4 failed for Policy Rules!"


def downgrade() -> None:
    "Revert every place that refers to data uses."
    loop = asyncio.get_running_loop()
    asyncio.ensure_future(downgrade_privacy_declarations(), loop=loop)
    asyncio.ensure_future(downgrade_policy_rules(), loop=loop)
    pass
