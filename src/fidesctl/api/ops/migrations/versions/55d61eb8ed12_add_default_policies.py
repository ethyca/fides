"""add default policies

Revision ID: 55d61eb8ed12
Revises: b3b68c87c4a0
Create Date: 2022-06-13 19:26:24.197262

"""
import logging
from typing import Optional, Tuple
from uuid import uuid4

from alembic import op
from fideslib.cryptography.cryptographic_util import (
    generate_salt,
    generate_secure_random_string,
    hash_with_salt,
)
from fideslib.db.base_class import FidesBase
from fidesctl.api.ops.api.v1.scope_registry import SCOPE_REGISTRY
from fidesctl.api.ops.core.config import config
from fidesctl.api.ops.db.base import Policy, Rule, RuleTarget, StorageConfig
from fidesctl.api.ops.db.base_class import JSONTypeOverride
from fidesctl.api.ops.models.policy import ActionType, DrpAction
from fidesctl.api.ops.schemas.storage.storage import StorageType
from fidesctl.api.ops.service.masking.strategy.masking_strategy_string_rewrite import (
    STRING_REWRITE_STRATEGY_NAME,
)
from fidesctl.api.ops.util.data_category import DataCategory
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import LegacyRow
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.elements import TextClause
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesGcmEngine

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

revision = "55d61eb8ed12"
down_revision = "b3b68c87c4a0"
branch_labels = None
depends_on = None

FIDESOPS_AUTOGENERATED_CLIENT_KEY = "fidesops_autogenerated_client"
FIDESOPS_AUTOGENERATED_STORAGE_KEY = "fidesops_autogenerated_storage_destination"
AUTOGENERATED_ACCESS_KEY = "download"
AUTOGENERATED_ERASURE_KEY = "delete"

client_select_query: TextClause = text(
    """SELECT client.id FROM client WHERE fides_key = :fides_key"""
)

client_insert_query: TextClause = text(
    """
    INSERT INTO client (id, hashed_secret, salt, scopes, fides_key) 
    VALUES (:client_id, :hashed_secret, :salt, :scopes, :fides_key)
    """
)

client_delete_query: TextClause = text(
    """DELETE FROM client WHERE client.id = :client_id"""
)

storage_select_query: TextClause = text(
    """SELECT storageconfig.id FROM storageconfig WHERE storageconfig.key = :storage_config_key"""
)
storage_insert_query: TextClause = text(
    """
    INSERT INTO storageconfig(id, name, type, details, key, secrets, format) 
    VALUES(:storage_config_id, :storage_name, :storage_type, '{"naming": "request_id"}', 
    :storage_key, NULL, 'json')
    """
)
storage_delete_query: TextClause = text(
    """DELETE FROM storageconfig WHERE storageconfig.id = :storage_id"""
)
policy_select_query: TextClause = text(
    """
    SELECT policy.id FROM policy WHERE policy.key = :policy_key AND client_id = :client_id
    """
)
policy_insert_query: TextClause = text(
    """
    INSERT INTO policy(id, name, key, drp_action, client_id) 
    VALUES(:policy_id, :policy_name, :key, :drp_action, :client_id)
    """
)
rule_select_query = text("""SELECT rule.id FROM rule where policy_id = :policy_id""")
rule_insert_query: TextClause = text(
    """
    INSERT INTO rule (id, name, key, policy_id, action_type, masking_strategy, storage_destination_id, client_id) 
    VALUES (:rule_id, :rule_name, :rule_key, :policy_id, :action_type, :masking_strategy, :storage_id, :client_id)
    """
)
rule_target_insert_query: TextClause = text(
    """
    INSERT INTO ruletarget (id, name, key, data_category, rule_id, client_id) 
    VALUES (:target_id, :target_name, :target_key, :data_category, :rule_id, :client_id)
    """
)

delete_policy_query = text("""DELETE FROM policy WHERE policy.id = :policy_id""")
delete_rule_query = text("""DELETE FROM rule WHERE policy_id = :policy_id""")
delete_target_query = text("""DELETE FROM ruletarget WHERE rule_id IN :rule_ids""")


def generate_uuid(cls: FidesBase) -> str:
    """
    Generates a uuid with a prefix based on the tablename to be used as the
    record's ID value
    """
    try:
        prefix = f"{cls.__tablename__[:3]}_"
    except AttributeError:
        prefix = ""
    uuid = str(uuid4())
    return f"{prefix}{uuid}"


def upgrade() -> None:
    """Data migration only.

    Create an autogenerated client and storage destination, then use those to create
    autogenerated 'download' and 'delete' policies if they don't already exist."""
    if config.is_test_mode:
        logger.info(f"Skipping data migration in test mode (pytest)'")
        return

    connection: Connection = op.get_bind()
    storage_config_id: str = autogenerate_local_storage(connection)
    client_id: str = autogenerate_client(connection)

    policy_query_by_key: TextClause = text(
        """SELECT policy.id FROM policy WHERE policy.key = :policy_key"""
    )
    access_results: Optional[LegacyRow] = connection.execute(
        policy_query_by_key, {"policy_key": AUTOGENERATED_ACCESS_KEY}
    ).first()
    if not access_results:
        # Only create a "download" policy if one does not already exist
        autogenerate_access_policy(connection, client_id, storage_config_id)

    erasure_results: Optional[LegacyRow] = connection.execute(
        policy_query_by_key, {"policy_key": AUTOGENERATED_ERASURE_KEY}
    ).first()
    if not erasure_results:
        # Only create a "delete" policy if one does not already exist
        autogenerate_erasure_policy(connection, client_id)


def downgrade() -> None:
    """Data migration only.

    Remove 'download' and delete' policies if they were created by the autogenerated client, and then
    attempt to remove the autogenerated client and local storage destination.
    """
    if config.is_test_mode:
        logger.info(f"Skipping data migration in test mode (pytest)'")
        return

    connection: Connection = op.get_bind()
    client_result: Optional[LegacyRow] = connection.execute(
        client_select_query, {"fides_key": FIDESOPS_AUTOGENERATED_CLIENT_KEY}
    ).first()

    if not client_result:
        logger.info(f"No autogenerated client: '{FIDESOPS_AUTOGENERATED_CLIENT_KEY}'")
        return

    access_policy_result: Optional[LegacyRow] = connection.execute(
        policy_select_query,
        {"policy_key": AUTOGENERATED_ACCESS_KEY, "client_id": client_result[0]},
    ).first()

    if access_policy_result:
        logger.info(
            f"Deleting autogenerated '{AUTOGENERATED_ACCESS_KEY}' access policy"
        )
        access_rules: Tuple = tuple(
            [
                rul.id
                for rul in connection.execute(
                    rule_select_query, {"policy_id": access_policy_result[0]}
                )
            ]
        )

        # Only delete "download" policy if it was created by the autogenerated client
        connection.execute(delete_target_query, {"rule_ids": access_rules})
        connection.execute(delete_rule_query, {"policy_id": access_policy_result[0]})
        connection.execute(delete_policy_query, {"policy_id": access_policy_result[0]})

    erasure_policy_result: Optional[LegacyRow] = connection.execute(
        policy_select_query,
        {"policy_key": AUTOGENERATED_ERASURE_KEY, "client_id": client_result[0]},
    ).first()

    if erasure_policy_result:
        # Only delete "delete" policy if it was created by the autogenerated client
        logger.info(
            f"Deleting autogenerated '{AUTOGENERATED_ERASURE_KEY}' erasure policy"
        )
        erasure_rules: Tuple = tuple(
            [
                rul.id
                for rul in connection.execute(
                    rule_select_query, {"policy_id": erasure_policy_result[0]}
                )
            ]
        )
        connection.execute(delete_target_query, {"rule_ids": erasure_rules})
        connection.execute(delete_rule_query, {"policy_id": erasure_policy_result[0]})
        connection.execute(delete_policy_query, {"policy_id": erasure_policy_result[0]})

    try:
        logger.info(
            f"Deleting autogenerated client: '{FIDESOPS_AUTOGENERATED_CLIENT_KEY}'"
        )
        connection.execute(client_delete_query, {"client_id": client_result[0]})

        storage_result: Optional[LegacyRow] = connection.execute(
            storage_select_query,
            {"storage_config_key": FIDESOPS_AUTOGENERATED_STORAGE_KEY},
        ).first()
        if storage_result:
            logger.info(
                f"Deleting autogenerated local storage: '{FIDESOPS_AUTOGENERATED_STORAGE_KEY}'"
            )
            connection.execute(storage_delete_query, {"storage_id": storage_result[0]})
    except Exception:
        # It's possible the client or storage config have been attached to other things
        pass


def autogenerate_access_policy(
    connection: Connection, client_id: str, storage_id: str
) -> None:
    """Create an autogenerated 'download' access policy, with an access rule attached,
    targeting user data"""
    logger.info(f"Creating autogenerated '{AUTOGENERATED_ACCESS_KEY}' policy")

    policy_id: str = generate_uuid(Policy)
    connection.execute(
        policy_insert_query,
        {
            "policy_id": policy_id,
            "policy_name": "Fidesops Autogenerated Access Policy",
            "key": AUTOGENERATED_ACCESS_KEY,
            "drp_action": DrpAction.access.value,
            "client_id": client_id,
        },
    )

    rule_id: str = generate_uuid(Rule)
    connection.execute(
        rule_insert_query,
        {
            "rule_id": rule_id,
            "rule_key": "fidesops_autogenerated_access_rule",
            "rule_name": "Fidesops Autogenerated Access Rule",
            "policy_id": policy_id,
            "action_type": ActionType.access.value,
            "storage_id": storage_id,
            "client_id": client_id,
            "masking_strategy": None,
        },
    )

    rule_target_id = generate_uuid(RuleTarget)
    connection.execute(
        rule_target_insert_query,
        {
            "target_id": rule_target_id,
            "target_name": "Fidesops Autogenerated Access Target",
            "target_key": "fidesops_autogenerated_access_target",
            "data_category": DataCategory("user").value,
            "rule_id": rule_id,
            "client_id": client_id,
        },
    )


def autogenerate_erasure_policy(connection: Connection, client_id: str) -> None:
    """Create an autogenerated 'deletion' erasure policy, with an erasure rule attached,
    targeting user data"""
    logger.info(f"Creating autogenerated '{AUTOGENERATED_ERASURE_KEY}' policy")

    policy_id: str = generate_uuid(Policy)
    connection.execute(
        policy_insert_query,
        {
            "policy_id": policy_id,
            "policy_name": "Fidesops Autogenerated Erasure Policy",
            "key": AUTOGENERATED_ERASURE_KEY,
            "drp_action": DrpAction.deletion.value,
            "client_id": client_id,
        },
    )

    rule_id: str = generate_uuid(Rule)
    encryption: StringEncryptedType = StringEncryptedType(
        JSONTypeOverride, config.security.app_encryption_key, AesGcmEngine, "pkcs5"
    )
    connection.execute(
        rule_insert_query,
        {
            "rule_id": rule_id,
            "rule_name": "Fidesops Autogenerated Erasure Rule",
            "rule_key": "fidesops_autogenerated_erasure_rule",
            "policy_id": policy_id,
            "action_type": ActionType.erasure.value,
            "client_id": client_id,
            "storage_id": None,
            "masking_strategy": encryption.process_bind_param(
                {
                    "strategy": STRING_REWRITE_STRATEGY_NAME,
                    "configuration": {"rewrite_value": "MASKED"},
                },
                postgresql,
            ),
        },
    )

    rule_target_id: str = generate_uuid(Rule)
    connection.execute(
        rule_target_insert_query,
        {
            "target_id": rule_target_id,
            "target_name": "Fidesops Autogenerated Erasure Target",
            "target_key": "fidesops_autogenerated_erasure_target",
            "data_category": "user.provided.identifiable",
            "rule_id": rule_id,
            "client_id": client_id,
        },
    )


def autogenerate_local_storage(connection: Connection) -> str:
    """Generate local storage for the access rule"""
    logger.info(
        f"Creating autogenerated local storage: '{FIDESOPS_AUTOGENERATED_STORAGE_KEY}'"
    )

    storage_config_id: str = generate_uuid(StorageConfig)
    connection.execute(
        storage_insert_query,
        {
            "storage_config_id": storage_config_id,
            "storage_key": FIDESOPS_AUTOGENERATED_STORAGE_KEY,
            "storage_type": StorageType.local.value,
            "storage_name": "Fidesops Autogenerated Local Storage",
        },
    )
    return storage_config_id


def autogenerate_client(connection: Connection) -> str:
    """Generate a client for creating policies, rules, and ruletargets"""
    logger.info(f"Creating autogenerated client: '{FIDESOPS_AUTOGENERATED_CLIENT_KEY}'")

    client_id: str = generate_secure_random_string(
        config.security.oauth_client_id_length_bytes
    )
    secret: str = generate_secure_random_string(
        config.security.oauth_client_secret_length_bytes
    )
    salt: str = generate_salt()
    connection.execute(
        client_insert_query,
        {
            "client_id": client_id,
            "hashed_secret": hash_with_salt(
                secret.encode(config.security.encoding),
                salt.encode(config.security.encoding),
            ),
            "salt": salt,
            "scopes": SCOPE_REGISTRY,
            "fides_key": FIDESOPS_AUTOGENERATED_CLIENT_KEY,
        },
    )
    return client_id
