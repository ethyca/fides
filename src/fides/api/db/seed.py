"""
Provides functions that seed the application with data.
"""

from typing import Dict, List, Optional

from fideslang.default_taxonomy import DEFAULT_TAXONOMY
from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from fides.api.api.v1.endpoints.dataset_endpoints import patch_dataset_configs
from fides.api.api.v1.endpoints.saas_config_endpoints import (
    instantiate_connection_from_template,
)
from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.db.base_class import FidesBase
from fides.api.db.ctl_session import sync_session
from fides.api.db.system import upsert_system
from fides.api.models.client import ClientDetail
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.policy import Policy, Rule, RuleTarget
from fides.api.models.sql_models import (  # type: ignore[attr-defined]
    Dataset,
    System,
    sql_model_map,
)
from fides.api.oauth.roles import OWNER
from fides.api.schemas.connection_configuration.connection_config import (
    CreateConnectionConfigurationWithSecrets,
)
from fides.api.schemas.connection_configuration.saas_config_template_values import (
    SaasConnectionTemplateValues,
)
from fides.api.schemas.dataset import DatasetConfigCtlDataset
from fides.api.schemas.policy import ActionType, DrpAction
from fides.api.util.connection_util import patch_connection_configs
from fides.api.util.errors import AlreadyExistsError, QueryError
from fides.api.util.text import to_snake_case
from fides.config import CONFIG

from .crud import create_resource, get_resource, list_resource, upsert_resources
from .samples import (
    load_sample_connections_from_project,
    load_sample_resources_from_project,
)

DEFAULT_OAUTH_CLIENT_KEY = "default_oauth_client"
DEFAULT_ACCESS_POLICY = "default_access_policy"
DEFAULT_ACCESS_POLICY_RULE = "default_access_policy_rule"
DEFAULT_ERASURE_POLICY = "default_erasure_policy"
DEFAULT_ERASURE_POLICY_RULE = "default_erasure_policy_rule"
DEFAULT_ERASURE_MASKING_STRATEGY = "hmac"

DEFAULT_CONSENT_POLICY: str = "default_consent_policy"
DEFAULT_CONSENT_RULE = "default_consent_rule"


def create_or_update_parent_user() -> None:
    with sync_session() as db_session:
        if (
            not CONFIG.security.parent_server_username
            and not CONFIG.security.parent_server_password
        ):
            return

        if (
            CONFIG.security.parent_server_username
            and not CONFIG.security.parent_server_password
            or CONFIG.security.parent_server_password
            and not CONFIG.security.parent_server_username
        ):
            # Both log and raise are here because the raise message is not showing.
            # It could potentially be related to https://github.com/ethyca/fides/issues/1228
            log.error(
                "Both a parent_server_user and parent_server_password must be set to create a parent server user"
            )
            raise ValueError(
                "Both a parent_server_user and parent_server_password must be set to create a parent server user"
            )

        user = (
            FidesUser.get_by(
                db_session,
                field="username",
                value=CONFIG.security.parent_server_username,
            )
            if CONFIG.security.parent_server_username
            else None
        )

        if user and CONFIG.security.parent_server_password:
            if not user.credentials_valid(CONFIG.security.parent_server_password):
                log.debug("Updating Fides parent user credentials")
                user.update_password(db_session, CONFIG.security.parent_server_password)
                return
            # clean exit if parent user already exists and credentials match
            return

        log.debug("Creating Fides parent user credentials")
        user = FidesUser.create(
            db=db_session,
            data={
                "username": CONFIG.security.parent_server_username,
                "password": CONFIG.security.parent_server_password,
            },
        )
        FidesUserPermissions.create(
            db=db_session,
            data={"user_id": user.id, "roles": [OWNER]},
        )


def filter_data_categories(
    categories: List[str], excluded_categories: List[str]
) -> List[str]:
    """
    Filter data categories and their children out of a list of categories.

    We only want user-related data categories, but not the parent category
    We also only want 2nd level categories, otherwise there are policy conflicts
    """
    user_categories = [
        category
        for category in categories
        if category.startswith("user.") and len(category.split(".")) < 3
    ]
    if excluded_categories:
        duplicated_categories = [
            category
            for excluded_category in excluded_categories
            for category in user_categories
            if not category.startswith(excluded_category)
        ]
        default_categories = {
            category
            for category in duplicated_categories
            if duplicated_categories.count(category) == len(excluded_categories)
        }
        return sorted(list(default_categories))
    return sorted(user_categories)


def get_client_id(db_session: Session) -> str:
    client = ClientDetail.get_by(
        db=db_session,
        field="fides_key",
        value=DEFAULT_OAUTH_CLIENT_KEY,
    )
    if not client:
        client, _ = ClientDetail.create_client_and_secret(
            db=db_session,
            client_id_byte_length=CONFIG.security.oauth_client_id_length_bytes,
            client_secret_byte_length=CONFIG.security.oauth_client_secret_length_bytes,
            fides_key=DEFAULT_OAUTH_CLIENT_KEY,
        )

    return client.id


def load_default_access_policy(
    db_session: Session, client_id: str, default_data_categories: List[str]
) -> None:
    access_policy: Optional[FidesBase] = Policy.get_by(
        db_session, field="key", value=DEFAULT_ACCESS_POLICY
    )
    if not access_policy:
        log.info(f"Creating default policy: {DEFAULT_ACCESS_POLICY}...")
        access_policy = Policy.create(
            db=db_session,
            data={
                "name": "Default Access Policy",
                "key": DEFAULT_ACCESS_POLICY,
                "execution_timeframe": 45,
                "client_id": client_id,
                "drp_action": DrpAction.access.value,
            },
        )
    else:
        log.debug(
            f"Skipping {DEFAULT_ACCESS_POLICY} creation as it already exists in the database"
        )

    access_rule: Optional[FidesBase] = Rule.get_by(
        db_session, field="key", value=DEFAULT_ACCESS_POLICY_RULE
    )
    if not access_rule:
        log.info(f"Creating default policy rule: {DEFAULT_ACCESS_POLICY_RULE}...")
        access_rule = Rule.create(
            db=db_session,
            data={
                "action_type": ActionType.access.value,
                "name": "Default Access Rule",
                "key": DEFAULT_ACCESS_POLICY_RULE,
                "policy_id": access_policy.id,
                "client_id": client_id,
            },
        )

        log.info("Creating default policy rules targets...")
        for target in default_data_categories:
            data = {
                "data_category": target,
                "rule_id": access_rule.id,
            }
            compound_key = to_snake_case(RuleTarget.get_compound_key(data=data))
            data["key"] = compound_key
            try:
                RuleTarget.create(
                    db=db_session,
                    data=data,
                )
            except KeyOrNameAlreadyExists:  # pragma: no cover
                # This rule target already exists against the Policy
                pass
    else:
        log.debug(
            f"Skipping {DEFAULT_ACCESS_POLICY_RULE} creation as it already exists in the database"
        )


def load_default_erasure_policy(
    db_session: Session, client_id: str, default_data_categories: List[str]
) -> None:
    erasure_policy: Optional[FidesBase] = Policy.get_by(
        db_session, field="key", value=DEFAULT_ERASURE_POLICY
    )
    if not erasure_policy:
        log.info(f"Creating default policy: {DEFAULT_ERASURE_POLICY}...")
        erasure_policy = Policy.create(
            db=db_session,
            data={
                "name": "Default Erasure Policy",
                "key": DEFAULT_ERASURE_POLICY,
                "execution_timeframe": 45,
                "client_id": client_id,
                "drp_action": DrpAction.deletion.value,
            },
        )
    else:
        log.debug(
            f"Skipping {DEFAULT_ERASURE_POLICY} creation as it already exists in the database"
        )

    erasure_rule: Optional[FidesBase] = Rule.get_by(
        db_session, field="key", value=DEFAULT_ERASURE_POLICY_RULE
    )
    if not erasure_rule:
        log.info(f"Creating default policy rule: {DEFAULT_ERASURE_POLICY_RULE}...")
        erasure_rule = Rule.create(
            db=db_session,
            data={
                "action_type": ActionType.erasure.value,
                "name": "Default Erasure Rule",
                "key": DEFAULT_ERASURE_POLICY_RULE,
                "policy_id": erasure_policy.id,
                "client_id": client_id,
                "masking_strategy": {
                    "strategy": DEFAULT_ERASURE_MASKING_STRATEGY,
                    "configuration": {},
                },
            },
        )

        log.info("Creating default policy rule targets...")
        for target in default_data_categories:
            data = {
                "data_category": target,
                "rule_id": erasure_rule.id,
            }
            compound_key = to_snake_case(RuleTarget.get_compound_key(data=data))
            data["key"] = compound_key
            try:
                RuleTarget.create(
                    db=db_session,
                    data=data,
                )
            except KeyOrNameAlreadyExists:  # pragma: no cover
                # This rule target already exists against the Policy
                pass
    else:
        log.debug(
            f"Skipping {DEFAULT_ERASURE_POLICY_RULE} creation as it already exists in the database"
        )

    log.info(f"Creating default policy: {DEFAULT_CONSENT_POLICY}...")
    consent_policy = Policy.create_or_update(
        db=db_session,
        data={
            "name": "Default Consent Policy",
            "key": DEFAULT_CONSENT_POLICY,
            "execution_timeframe": 45,
            "client_id": client_id,
        },
    )

    log.info(f"Creating default policy rule: {DEFAULT_CONSENT_RULE}...")
    Rule.create_or_update(
        db=db_session,
        data={
            "action_type": ActionType.consent.value,
            "name": "Default Consent Rule",
            "key": DEFAULT_CONSENT_RULE,
            "policy_id": consent_policy.id,
            "client_id": client_id,
        },
    )


def load_default_dsr_policies() -> None:
    """
    Checks whether DSR execution policies exist in the database, and
    inserts them to target a default set of data categories if not.
    """
    with sync_session() as db_session:  # type: ignore[attr-defined]
        client_id = get_client_id(db_session)

        # By default, include all categories *except* those related to a user's
        # financial, payment, and credentials data. These are typically not
        # included in access and erasure requests as they are covered by other
        # compliance programs (e.g. legal, tax, security) and most
        # organizations need to be extra careful about how these are used -
        # especially for erasure! Therefore, a safe default for "out of the
        # box" behaviour is to exclude these
        excluded_data_categories = [
            "user.financial",
            "user.payment",
            "user.authorization",
        ]
        all_data_categories = [
            str(category.fides_key) for category in DEFAULT_TAXONOMY.data_category
        ]
        default_data_categories = filter_data_categories(
            all_data_categories, excluded_data_categories
        )
        log.debug(
            f"Preparing to create default rules for the following Data Categories: {default_data_categories} if they do not already exist"
        )

        load_default_access_policy(db_session, client_id, default_data_categories)
        load_default_erasure_policy(db_session, client_id, default_data_categories)

        log.info("All default policies & rules created")


async def load_default_organization(async_session: AsyncSession) -> None:
    """
    Seed the database with a default organization unless
    one with a matching name already exists.
    """

    log.info("Loading the default organization...")
    organizations: List[Dict] = list(map(dict, DEFAULT_TAXONOMY.dict()["organization"]))

    inserted = 0
    for org in organizations:
        try:
            existing = await get_resource(
                sql_model_map["organization"],
                org["fides_key"],
                async_session,
                raise_not_found=False,
            )
            if not existing:
                await create_resource(sql_model_map["organization"], org, async_session)
                inserted += 1
        except AlreadyExistsError:
            pass

    log.debug(f"INSERTED {inserted} organization resource(s)")
    log.debug(f"SKIPPED {len(organizations)-inserted} organization resource(s)")


async def load_default_taxonomy(async_session: AsyncSession) -> None:
    """Seed the database with the default taxonomy resources."""

    upsert_resource_types = list(DEFAULT_TAXONOMY.__fields_set__)
    upsert_resource_types.remove("organization")

    log.info("Loading the default fideslang taxonomy resources...")
    for resource_type in upsert_resource_types:
        log.debug(f"Processing {resource_type} resources...")
        default_resources = DEFAULT_TAXONOMY.dict()[resource_type]
        existing_resources = await list_resource(
            sql_model_map[resource_type], async_session
        )
        existing_keys = [item.fides_key for item in existing_resources]
        resources = [
            resource
            for resource in default_resources
            if resource["fides_key"] not in existing_keys
        ]

        if len(resources) == 0:
            log.debug(f"No new {resource_type} resources to add from default taxonomy.")
            continue

        try:
            await upsert_resources(
                sql_model_map[resource_type], resources, async_session
            )
        except QueryError:  # pragma: no cover
            pass  # The create_resource function will log the error
        else:
            log.debug(f"UPSERTED {len(resources)} {resource_type} resource(s)")


async def load_default_resources(async_session: AsyncSession) -> None:
    """
    Seed the database with default resources that the application
    expects to be available.
    """
    await load_default_organization(async_session)
    await load_default_taxonomy(async_session)
    load_default_dsr_policies()


async def load_samples(async_session: AsyncSession) -> None:
    # pylint: disable=too-many-branches, too-many-statements
    log.info("Loading sample resources...")
    try:
        sample_resources = dict(load_sample_resources_from_project())
        for resource_type, resources in sample_resources.items():
            if len(resources):
                if resource_type == "system":
                    await upsert_system(resources, async_session)
                else:
                    await upsert_resources(
                        sql_model_map[resource_type],
                        [e.dict() for e in resources],
                        async_session,
                    )
    except QueryError:  # pragma: no cover
        pass  # The upsert_resources function will log any error

    log.info("Loading sample connections...")
    try:
        sample_connections = load_sample_connections_from_project()
        with sync_session() as db_session:
            for connection in sample_connections:
                assert connection.key, "Connection Key expected!"
                # If the connection config already exists, skip creation!
                # NOTE: This creates an edge case where the sample data was
                # created previously, but has since changed. By not deleting &
                # recreating here, we allow the "old" data to persist. That's an
                # acceptable risk here, so we log an INFO message to provide a
                # breadcrumb back to this code.
                connection_config: Optional[ConnectionConfig] = ConnectionConfig.get_by(
                    db=db_session, field="key", value=connection.key
                )
                if connection_config:
                    log.debug(
                        f"Sample connection '{connection.key}' already exists, skipping..."
                    )
                    continue

                # For SaaS connections, reuse our "instantiate from template" API
                if (
                    connection.connection_type == "saas"
                    and connection.saas_connector_type
                ):
                    log.debug(
                        f"Loading sample connection with SaaS connection type '{connection.saas_connector_type}'..."
                    )
                    saas_template_data = dict(connection)
                    saas_template_data["instance_key"] = connection.key
                    saas_template_data.pop(
                        "dataset", None
                    )  # not supported by this API!
                    saas_template_data.pop(
                        "system_key", None
                    )  # not supported by this API!
                    instantiate_connection_from_template(
                        db=db_session,
                        saas_connector_type=connection.saas_connector_type,
                        template_values=SaasConnectionTemplateValues.parse_obj(
                            saas_template_data
                        ),
                    )

                    # Check that it succeeded!
                    connection_config = ConnectionConfig.get_by(
                        db=db_session, field="key", value=connection.key
                    )
                    if not connection_config:
                        log.debug(
                            f"Failed to create sample connection '{connection.key}'"
                        )
                    continue

                # For non-SaaS connections, reuse our connection & dataset APIs
                log.debug(
                    f"Loading sample connection with type '{connection.connection_type}'..."
                )
                connection_config_data = dict(connection)
                connection_config_data.pop(
                    "dataset", None
                )  # not supported by this API!
                connection_config_data.pop(
                    "system_key", None
                )  # not supported by this API!
                patch_connection_configs(
                    db=db_session,
                    configs=[
                        CreateConnectionConfigurationWithSecrets.parse_obj(
                            connection_config_data
                        )
                    ],
                )

                # Check that it succeeded!
                connection_config = ConnectionConfig.get_by(
                    db=db_session, field="key", value=connection.key
                )
                if not connection_config:
                    log.debug(f"Failed to create sample connection '{connection.key}'")
                    continue

                # Create the DatasetConfig by linking to an existing Dataset
                dataset_key = connection.dataset
                if dataset_key:
                    log.debug(
                        f"Linking sample connection with key '{connection.key}' to dataset '{dataset_key}'..."
                    )
                    dataset = Dataset.get_by(
                        db=db_session, field="fides_key", value=dataset_key
                    )
                    if not dataset:
                        log.debug(
                            f"Could not find existing dataset '{dataset_key}' for sample connection '{connection.key}'"
                        )
                        continue

                    dataset_pair = DatasetConfigCtlDataset(
                        fides_key=dataset_key, ctl_dataset_fides_key=dataset_key
                    )
                    patch_dataset_configs(
                        dataset_pairs=[dataset_pair],
                        db=db_session,
                        connection_config=connection_config,
                    )
                    dataset_config = DatasetConfig.get_by(
                        db=db_session, field="fides_key", value=dataset_key
                    )
                    if not dataset_config:
                        log.debug(
                            f"Failed to create dataset config '{dataset_key}' for sample connection '{connection.key}'"
                        )
                        continue

                # Link the connection to an existing system
                system_key = connection.system_key
                if system_key:
                    log.debug(
                        f"Linking sample connection with key '{connection.key}' to system '{system_key}'..."
                    )
                    system = System.get_by(
                        db=db_session, field="fides_key", value=system_key
                    )
                    if not system:
                        log.debug(
                            f"Could not find existing system '{system_key}' for sample connection '{connection.key}'"
                        )
                        continue

                    linked_connection_config = ConnectionConfig.create_or_update(
                        db=db_session,
                        data={
                            **connection_config.__dict__,
                            **{"system_id": system.id},
                        },
                        check_name=False,
                    )
                    if not linked_connection_config:
                        log.debug(
                            f"Failed to link sample connection '{connection.key}' to system '{system_key}'"
                        )
                        continue

    except QueryError:  # pragma: no cover
        pass  # The upsert_resources function will log any error
