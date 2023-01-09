"""
Provides functions that seed the application with data.
"""
from typing import List

from fideslang import DEFAULT_TAXONOMY
from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.ctl.database.session import sync_session
from fides.api.ctl.sql_models import sql_model_map  # type: ignore[attr-defined]
from fides.api.ctl.utils.errors import AlreadyExistsError, QueryError
from fides.api.ops.api.v1.scope_registry import (
    PRIVACY_REQUEST_CREATE,
    PRIVACY_REQUEST_READ,
    PRIVACY_REQUEST_TRANSFER,
)
from fides.api.ops.models.policy import ActionType, DrpAction, Policy, Rule, RuleTarget
from fides.api.ops.models.storage import StorageConfig
from fides.api.ops.schemas.storage.storage import (
    FileNaming,
    ResponseFormat,
    StorageDetails,
    StorageType,
)
from fides.core.config import get_config
from fides.lib.exceptions import KeyOrNameAlreadyExists
from fides.lib.models.client import ClientDetail
from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions
from fides.lib.utils.text import to_snake_case

from .crud import create_resource, list_resource

CONFIG = get_config()
FIDESOPS_AUTOGENERATED_CLIENT_KEY = "default_oauth_client"
DEFAULT_STORAGE_KEY = "default_local_storage"
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
                log.info("Updating parent user")
                user.update_password(db_session, CONFIG.security.parent_server_password)
                return
            # clean exit if parent user already exists and credentials match
            return

        log.info("Creating parent user")
        user = FidesUser.create(
            db=db_session,
            data={
                "username": CONFIG.security.parent_server_username,
                "password": CONFIG.security.parent_server_password,
            },
        )
        FidesUserPermissions.create(
            db=db_session,
            data={
                "user_id": user.id,
                "scopes": [
                    PRIVACY_REQUEST_CREATE,
                    PRIVACY_REQUEST_READ,
                    PRIVACY_REQUEST_TRANSFER,
                ],
            },
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


async def load_default_dsr_policies() -> None:
    """
    Checks whether DSR execution policies exist in the database, and
    inserts them to target a default set of data categories if not.
    """
    with sync_session() as db_session:  # type: ignore[attr-defined]

        client = ClientDetail.get_by(
            db=db_session,
            field="fides_key",
            value=FIDESOPS_AUTOGENERATED_CLIENT_KEY,
        )
        if not client:
            client, _ = ClientDetail.create_client_and_secret(
                db=db_session,
                client_id_byte_length=CONFIG.security.oauth_client_id_length_bytes,
                client_secret_byte_length=CONFIG.security.oauth_client_secret_length_bytes,
                fides_key=FIDESOPS_AUTOGENERATED_CLIENT_KEY,
            )

        client_id = client.id

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
            "user.credentials",
        ]
        all_data_categories = [
            str(category.fides_key) for category in DEFAULT_TAXONOMY.data_category
        ]
        default_data_categories = filter_data_categories(
            all_data_categories, excluded_data_categories
        )
        log.info(
            f"Preparing to create default rules for the following Data Categories: {default_data_categories}"
        )

        log.info(f"Creating: {DEFAULT_ACCESS_POLICY}...")
        access_policy = Policy.create_or_update(
            db=db_session,
            data={
                "name": "Default Access Policy",
                "key": DEFAULT_ACCESS_POLICY,
                "execution_timeframe": 45,
                "client_id": client_id,
                "drp_action": DrpAction.access.value,
            },
        )

        log.info(f"Creating: {DEFAULT_STORAGE_KEY}...")
        local_storage_config = StorageConfig.create_or_update(
            db=db_session,
            data={
                "name": "Default Local Storage Config",
                "key": DEFAULT_STORAGE_KEY,
                "type": StorageType.local,
                "details": {
                    StorageDetails.NAMING.value: FileNaming.request_id.value,
                },
                "format": ResponseFormat.json,
            },
        )

        log.info(f"Creating: {DEFAULT_ACCESS_POLICY_RULE}...")
        access_rule = Rule.create_or_update(
            db=db_session,
            data={
                "action_type": ActionType.access.value,
                "name": "Default Access Rule",
                "key": DEFAULT_ACCESS_POLICY_RULE,
                "policy_id": access_policy.id,
                "storage_destination_id": local_storage_config.id,
                "client_id": client_id,
            },
        )

        log.info("Creating: Data Category Access Rules...")
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
            except KeyOrNameAlreadyExists:
                # This rule target already exists against the Policy
                pass

        log.info(f"Creating: {DEFAULT_ERASURE_POLICY}...")
        erasure_policy = Policy.create_or_update(
            db=db_session,
            data={
                "name": "Default Erasure Policy",
                "key": DEFAULT_ERASURE_POLICY,
                "execution_timeframe": 45,
                "client_id": client_id,
                "drp_action": DrpAction.deletion.value,
            },
        )

        log.info(f"Creating: {DEFAULT_ERASURE_POLICY_RULE}...")
        erasure_rule = Rule.create_or_update(
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

        log.info("Creating: Data Category Erasure Rules...")
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
            except KeyOrNameAlreadyExists:
                # This rule target already exists against the Policy
                pass

        log.info("Creating: Default Consent Policy")
        consent_policy = Policy.create_or_update(
            db=db_session,
            data={
                "name": "Default Consent Policy",
                "key": DEFAULT_CONSENT_POLICY,
                "execution_timeframe": 45,
                "client_id": client_id,
            },
        )

        log.info("Creating: Default Consent Rule")
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

        log.info("All Policies & Rules Seeded.")


async def load_default_organization(async_session: AsyncSession) -> None:
    """
    Seed the database with a default organization unless
    one with a matching name already exists.
    """

    log.info("Creating the default organization...")
    organizations = list(map(dict, DEFAULT_TAXONOMY.dict()["organization"]))

    inserted = 0
    for org in organizations:
        try:
            await create_resource(sql_model_map["organization"], org, async_session)
            inserted += 1
        except AlreadyExistsError:
            pass

    log.info(f"INSERTED {inserted} organization resource(s)")
    log.info(f"SKIPPED {len(organizations)-inserted} organization resource(s)")


async def load_default_taxonomy(async_session: AsyncSession) -> None:
    """Seed the database with the default taxonomy resources."""

    upsert_resource_types = list(DEFAULT_TAXONOMY.__fields_set__)
    upsert_resource_types.remove("organization")

    log.info("INSERTING new default fideslang taxonomy resources")
    for resource_type in upsert_resource_types:
        log.info(f"Processing {resource_type} resources...")
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
            log.info(f"No new {resource_type} resources to add from default taxonomy.")
            continue

        try:
            for resource in resources:
                await create_resource(
                    sql_model_map[resource_type], resource, async_session
                )
        except QueryError:
            pass  # The create_resource function will log the error
        else:
            log.info(f"INSERTED {len(resources)} {resource_type} resource(s)")


async def load_default_resources(async_session: AsyncSession) -> None:
    """
    Seed the database with default resources that the application
    expects to be available.
    """
    await load_default_organization(async_session)
    await load_default_taxonomy(async_session)
    await load_default_dsr_policies()
