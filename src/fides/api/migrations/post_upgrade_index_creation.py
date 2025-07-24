import json
from typing import Dict, List

from loguru import logger
from redis.lock import Lock
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.db.session import get_db_session
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.api.util.lock import redis_lock
from fides.config import CONFIG

"""
This utility is used to detect indices or constraints that were deferred as part
of a standard Fides/Alembic migration.

The standard approach for creating indices or constraints on large tables is a blocking operation,
meaning reads and write can't run while the indices and constraints are being created.
A non-blocking approach is to use the CONCURRENTLY keyword for index creation then adding
the constraints with ADD CONSTRAINT USING INDEX.

However these approaches cannot run in a transaction, which is what Fides/Alembic uses to
apply migrations. The approach here is to run these commands after the application has started
up and commit the changes immediately, outside of a transaction.

The commands that need to run are denoted in the `TABLE_OBJECT_MAP`. Indices that are used
to create constraints also include the `constraint_name` value since either the presence of
the index or the constraint can be used to determine if an index has executed.
When using the ADD CONSTRAINT USING INDEX syntax, the index specified in the command is
automatically renamed to match the name of the constraint being added.
This means that after the constraint is created, the index will have the same name as the constraint.
"""

POST_UPGRADE_INDEX_CREATION = "post_upgrade_index_creation"

TABLE_OBJECT_MAP: Dict[str, List[Dict[str, str]]] = {
    "currentprivacypreferencev2": [
        {
            "name": "ix_currentprivacypreferencev2_email_property_id",
            "statement": "CREATE UNIQUE INDEX CONCURRENTLY ix_currentprivacypreferencev2_email_property_id ON currentprivacypreferencev2 (email, property_id)",
            "type": "index",
            "constraint_name": "last_saved_for_email_per_property_id",
        },
        {
            "name": "ix_currentprivacypreferencev2_external_id_property_id",
            "statement": "CREATE UNIQUE INDEX CONCURRENTLY ix_currentprivacypreferencev2_external_id_property_id ON currentprivacypreferencev2 (external_id, property_id)",
            "type": "index",
            "constraint_name": "last_saved_for_external_id_per_property_id",
        },
        {
            "name": "ix_currentprivacypreferencev2_fides_user_device_property_id",
            "statement": "CREATE UNIQUE INDEX CONCURRENTLY ix_currentprivacypreferencev2_fides_user_device_property_id ON currentprivacypreferencev2 (fides_user_device, property_id)",
            "type": "index",
            "constraint_name": "last_saved_for_fides_user_device_per_property_id",
        },
        {
            "name": "ix_currentprivacypreferencev2_phone_number_property_id",
            "statement": "CREATE UNIQUE INDEX CONCURRENTLY ix_currentprivacypreferencev2_phone_number_property_id ON currentprivacypreferencev2 (phone_number, property_id)",
            "type": "index",
            "constraint_name": "last_saved_for_phone_number_per_property_id",
        },
        {
            "name": "ix_currentprivacypreferencev2_hashed_external_id",
            "statement": "CREATE INDEX CONCURRENTLY ix_currentprivacypreferencev2_hashed_external_id ON currentprivacypreferencev2 (hashed_external_id)",
            "type": "index",
        },
        {
            "name": "last_saved_for_email_per_property_id",
            "statement": "ALTER TABLE currentprivacypreferencev2 ADD CONSTRAINT last_saved_for_email_per_property_id UNIQUE USING INDEX ix_currentprivacypreferencev2_email_property_id",
            "type": "constraint",
        },
        {
            "name": "last_saved_for_external_id_per_property_id",
            "statement": "ALTER TABLE currentprivacypreferencev2 ADD CONSTRAINT last_saved_for_external_id_per_property_id UNIQUE USING INDEX ix_currentprivacypreferencev2_external_id_property_id",
            "type": "constraint",
        },
        {
            "name": "last_saved_for_fides_user_device_per_property_id",
            "statement": "ALTER TABLE currentprivacypreferencev2 ADD CONSTRAINT last_saved_for_fides_user_device_per_property_id UNIQUE USING INDEX ix_currentprivacypreferencev2_fides_user_device_property_id",
            "type": "constraint",
        },
        {
            "name": "last_saved_for_phone_number_per_property_id",
            "statement": "ALTER TABLE currentprivacypreferencev2 ADD CONSTRAINT last_saved_for_phone_number_per_property_id UNIQUE USING INDEX ix_currentprivacypreferencev2_phone_number_property_id",
            "type": "constraint",
        },
    ],
    "privacypreferencehistory": [
        {
            "name": "ix_privacypreferencehistory_hashed_external_id",
            "statement": "CREATE INDEX CONCURRENTLY ix_privacypreferencehistory_hashed_external_id ON privacypreferencehistory (hashed_external_id)",
            "type": "index",
        },
    ],
    "servednoticehistory": [
        {
            "name": "ix_servednoticehistory_hashed_external_id",
            "statement": "CREATE INDEX CONCURRENTLY ix_servednoticehistory_hashed_external_id ON servednoticehistory (hashed_external_id)",
            "type": "index",
        },
    ],
    "stagedresourceancestor": [
        # primary key index
        {
            "name": "ix_staged_resource_ancestor_pkey",
            "statement": "CREATE UNIQUE INDEX CONCURRENTLY ix_staged_resource_ancestor_pkey ON stagedresourceancestor (id)",
            "type": "index",
        },
        # unique constraint + index
        {
            "name": "ix_staged_resource_ancestor_unique",
            "statement": "CREATE UNIQUE INDEX CONCURRENTLY ix_staged_resource_ancestor_unique ON stagedresourceancestor (ancestor_urn, descendant_urn)",
            "type": "index",
            "constraint_name": "uq_staged_resource_ancestor",
        },
        {
            "name": "uq_staged_resource_ancestor",
            "statement": "ALTER TABLE stagedresourceancestor ADD CONSTRAINT uq_staged_resource_ancestor UNIQUE USING INDEX ix_staged_resource_ancestor_unique",
            "type": "constraint",
        },
        # foreign key constraints
        {
            "name": "fk_staged_resource_ancestor_ancestor",
            "statement": "ALTER TABLE stagedresourceancestor ADD CONSTRAINT fk_staged_resource_ancestor_ancestor FOREIGN KEY (ancestor_urn) REFERENCES stagedresource (urn) ON DELETE CASCADE",
            "type": "constraint",
        },
        {
            "name": "fk_staged_resource_ancestor_descendant",
            "statement": "ALTER TABLE stagedresourceancestor ADD CONSTRAINT fk_staged_resource_ancestor_descendant FOREIGN KEY (descendant_urn) REFERENCES stagedresource (urn) ON DELETE CASCADE",
            "type": "constraint",
        },
        # column indexes
        {
            "name": "ix_staged_resource_ancestor_ancestor",
            "statement": "CREATE INDEX CONCURRENTLY ix_staged_resource_ancestor_ancestor ON stagedresourceancestor (ancestor_urn)",
            "type": "index",
        },
        {
            "name": "ix_staged_resource_ancestor_descendant",
            "statement": "CREATE INDEX CONCURRENTLY ix_staged_resource_ancestor_descendant ON stagedresourceancestor (descendant_urn)",
            "type": "index",
        },
    ],
    "stagedresource": [
        {
            "name": "ix_stagedresource_monitor_config_resource_type_consent",
            "statement": "CREATE INDEX CONCURRENTLY ix_stagedresource_monitor_config_resource_type_consent ON stagedresource (monitor_config_id, resource_type, (meta->>'consent_aggregated'))",
            "type": "index",
        },
        {
            "name": "ix_stagedresource_system_vendor_consent",
            "statement": "CREATE INDEX CONCURRENTLY ix_stagedresource_system_vendor_consent ON stagedresource (system_id, vendor_id, (meta->>'consent_aggregated'))",
            "type": "index",
        },
    ],
}


def check_object_exists(db: Session, object_name: str) -> bool:
    """Checks Postgres' system catalogs to verify the existence of a given index or constraint in a specific table."""
    object_query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE indexname = :object_name
        ) OR EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = :object_name
        )
        """
    )
    result = db.execute(
        object_query,
        {
            "object_name": object_name,
        },
    ).scalar()
    return result


def create_object(db: Session, object_statement: str, object_name: str) -> None:
    """Executes the index or constraint creation statement."""
    logger.info(f"Creating index/constraint object: '{object_name}'...")
    with db.bind.connect().execution_options(
        isolation_level="AUTOCOMMIT"
    ) as connection:
        connection.execute(text(object_statement))
    logger.info(f"Successfully created index/constraint object: '{object_name}'")


def check_and_create_objects(
    db: Session, table_object_map: Dict[str, List[Dict[str, str]]], lock: Lock
) -> Dict[str, str]:
    """Returns a dictionary of any indices or constraints that were created."""
    object_info: Dict[str, str] = {}
    for _, objects in table_object_map.items():
        for object_data in objects:
            object_name = object_data["name"]
            object_statement = object_data["statement"]
            object_type = object_data["type"]
            object_exists = check_object_exists(db, object_name)

            if not object_exists:
                if object_type == "index":
                    constraint_name = object_data.get("constraint_name")
                    if constraint_name:
                        constraint_exists = check_object_exists(db, constraint_name)
                        if constraint_exists:
                            logger.debug(
                                f"Constraint {constraint_name} already exists, skipping index creation for {object_name}"
                            )
                            continue

                create_object(db, object_statement, object_name)
                object_info[object_name] = "created"
            else:
                logger.debug(
                    f"Object {object_name} already exists, skipping index/constraint creation"
                )
            lock.reacquire()

    return object_info


# Lock key for the post upgrade index creation
POST_UPGRADE_INDEX_CREATION_LOCK = "post_upgrade_index_creation_lock"
# The timeout of the lock for the post upgrade index creation, in seconds
POST_UPGRADE_INDEX_CREATION_LOCK_TIMEOUT_SECONDS = 600  # 10 minutes


def post_upgrade_index_creation_task() -> None:
    """
    Task for creating indices and constraints that were deferred
    as part of a standard Fides/Alembic migration.

    This task is to be kicked off as a background task during application startup,
    after standard migrations have been applied.

    If all specified indexes and constraints are created, the task is effectively
    a no-op, as it checks for the presence of the objects in the database before
    creating them.
    """
    with redis_lock(
        POST_UPGRADE_INDEX_CREATION_LOCK,
        POST_UPGRADE_INDEX_CREATION_LOCK_TIMEOUT_SECONDS,
    ) as lock:
        if not lock:
            return

        SessionLocal = get_db_session(CONFIG)
        with SessionLocal() as db:
            object_info: Dict[str, str] = check_and_create_objects(
                db, TABLE_OBJECT_MAP, lock
            )
            if object_info:
                logger.info(
                    f"Post upgrade index creation output: {json.dumps(object_info)}"
                )
            else:
                logger.debug("All indices and constraints already created")


def initiate_post_upgrade_index_creation() -> None:
    """Initiates scheduler to migrate all non-credential tables using a bcrypt hash to use a SHA-256 hash"""

    if CONFIG.test_mode:
        logger.debug("Skipping post upgrade index creation in test mode")
        return

    assert (
        scheduler.running
    ), "Scheduler is not running! Cannot migrate tables with bcrypt hashes."

    logger.info("Initiating scheduler for hash migration")
    scheduler.add_job(
        func=post_upgrade_index_creation_task,
        id=POST_UPGRADE_INDEX_CREATION,
    )
