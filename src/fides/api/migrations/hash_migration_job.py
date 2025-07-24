from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.api.deps import get_autoclose_db_session
from fides.api.db.base_class import FidesBase
from fides.api.migrations.hash_migration_mixin import HashMigrationMixin
from fides.api.migrations.hash_migration_tracker import HashMigrationTracker
from fides.api.models.privacy_preference import (
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
    ServedNoticeHistory,
)
from fides.api.models.privacy_request import CustomPrivacyRequestField, ProvidedIdentity
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.config import CONFIG

HASH_MIGRATION = "hash_migration"
MODELS_TO_MIGRATE = [
    CurrentPrivacyPreference,
    ProvidedIdentity,
    CustomPrivacyRequestField,
    PrivacyPreferenceHistory,
    ServedNoticeHistory,
]


def initiate_bcrypt_migration_task() -> None:
    """Initiates scheduler to migrate all non-credential tables using a bcrypt hash to use a SHA-256 hash"""

    if CONFIG.test_mode:
        return

    assert (
        scheduler.running
    ), "Scheduler is not running! Cannot migrate tables with bcrypt hashes."

    logger.info("Initiating scheduler for hash migration")
    scheduler.add_job(
        func=bcrypt_migration_task,
        id=HASH_MIGRATION,
    )


def bcrypt_migration_task() -> None:
    """
    Job to migrate all the tables using bcrypt hashes for general data (excludes tables with credentials).
    """

    with get_autoclose_db_session() as db:
        # Do a single pass to check if any of the models have already been migrated.
        # This will allow us to optimize searching for these models by not calling
        # the previously used bcrypt hash.
        for model in MODELS_TO_MIGRATE:
            if is_migrated(db, model):
                HashMigrationTracker.set_migrated(model.__name__)
                logger.info(f"{model.__name__} is already fully migrated.")

        # migrate remaining models
        for model in MODELS_TO_MIGRATE:
            if not HashMigrationTracker.is_migrated(model.__name__):
                migrate_table(db, model)  # type: ignore[arg-type]


def is_migrated(db: Session, model: type[FidesBase]) -> bool:
    """
    Checks the database to see if there exists at least one unmigrated row.
    """

    query = text(
        f"SELECT EXISTS (SELECT 1 FROM {model.__tablename__} WHERE is_hash_migrated IS FALSE)"
    )
    result = db.execute(query).scalar()
    return not result


def migrate_table(
    db: Session, model: type[HashMigrationMixin], batch_size: int = 1000
) -> None:
    """
    Migrate all unmigrated rows in the table corresponding to the passed in model.
    """

    while True:
        unmigrated_batch = (
            db.query(model)
            .filter(model.is_hash_migrated.is_(False))
            .limit(batch_size)
            .all()
        )
        if not unmigrated_batch:
            break

        for item in unmigrated_batch:
            item.migrate_hashed_fields()

        # commit after each batch is complete
        db.commit()

    HashMigrationTracker.set_migrated(model.__name__)
    logger.info(f"Completed hash migration for {model.__name__}.")
