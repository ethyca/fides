"""Upgrade to fideslang 1.4

Revision ID: 63b482f5b49b
Revises: 2661f31daffb
Create Date: 2023-05-26 07:51:25.947974

"""
from typing import Dict, List, Optional

from fideslang import DEFAULT_TAXONOMY
from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fides.api.ctl.sql_models import PrivacyDeclaration, PolicyCtl
import asyncio

from fides.api.api.v1.endpoints.dataset_endpoints import patch_dataset_configs
from fides.api.api.v1.endpoints.saas_config_endpoints import (
    instantiate_connection_from_template,
)
from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.ctl.database.session import async_session
from fides.api.ctl.database.system import upsert_system
from fides.api.ctl.sql_models import (  # type: ignore[attr-defined]
    Dataset,
    sql_model_map,
)
from fides.api.ctl.utils.errors import AlreadyExistsError, QueryError
from fides.api.db.base_class import FidesBase
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.policy import ActionType, DrpAction, Policy, Rule, RuleTarget
from fides.api.oauth.roles import OWNER
from fides.api.schemas.connection_configuration.connection_config import (
    CreateConnectionConfigurationWithSecrets,
    SaasConnectionTemplateValues,
)
from fides.api.schemas.dataset import DatasetConfigCtlDataset
from fides.api.util.connection_util import patch_connection_configs
from fides.api.util.text import to_snake_case
from fides.core.config import CONFIG

from fides.api.ctl.database.crud import (
    create_resource,
    get_resource,
    list_resource,
    upsert_resources,
)

from alembic import op
import sqlalchemy as sa
from collections import namedtuple
from typing import List


# revision identifiers, used by Alembic.
revision = "63b482f5b49b"
down_revision = "2661f31daffb"
branch_labels = None
depends_on = None

# The `key` is the old value, the `value` is the new value
data_use_updates: Dict[str, str] = {
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


async def update_privacy_declarations() -> None:
    async with async_session() as session:
        resources = await list_resource(PrivacyDeclaration, session)

        for resource in resources:
            current_data_use = resource.data_use

            if current_data_use in data_use_updates.keys():
                resource.data_use = data_use_updates[resource.data_use]

        await upsert_resources(PrivacyDeclaration, resources, session)

        # Since we can't write tests for data migrations, we do it live
        existing_resources = await list_resource(PrivacyDeclaration, session)
        assert not all(
            [
                False if resource.data_use in data_use_updates.keys() else True
                for resource in existing_resources
            ]
        ), "ERROR: Data Use Migration for Fideslang v1.4 failed for Privacy Declarations!"


async def update_policy_rules() -> None:
    async with async_session() as session:
        resources = await list_resource(PolicyCtl, session)
        for resource in resources:
            for rule in resource.rules:
                current_data_use = rule.data_use
                if current_data_use in data_use_updates.keys():
                    rule.data_use = data_use_updates[resource.data_use]
        await upsert_resources(PolicyCtl, resources, session)

        # Since we can't write tests for data migrations, we do it live
        existing_resources = await list_resource(PolicyCtl, session)
        assert not all(
            [
                False if rule.data_use in data_use_updates.keys() else True
                for resource in existing_resources
                for rule in resource
            ]
        ), "ERROR: Data Use Migration for Fideslang v1.4 failed for Policy Rules!"


def upgrade():
    # Update every place where an old data use could be

    loop = asyncio.get_running_loop()
    asyncio.ensure_future(update_privacy_declarations(), loop=loop)
    asyncio.ensure_future(update_policy_rules(), loop=loop)


def downgrade():
    pass
