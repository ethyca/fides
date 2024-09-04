from typing import Any

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from fides.api.migrations.hash_migration_tracker import HashMigrationTracker
from fides.api.models.privacy_preference import (
    CurrentPrivacyPreference,
    PrivacyPreferenceHistory,
    ServedNoticeHistory,
)
from fides.api.models.privacy_request import CustomPrivacyRequestField, ProvidedIdentity
from fides.api.tasks import DatabaseTask, celery_app
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


@celery_app.task(base=DatabaseTask, bind=True)
def bcrypt_migration_task(self: DatabaseTask) -> None:
    """
    Job to migrate all the tables using bcrypt hashes for general data (excludes tables with credentials).
    """

    with self.get_new_session() as db:
        # Do a single pass to check if any of the models have already been migrated.
        # This will allow us to optimize searching for these models by not calling
        # the previously used bcrypt hash.
        for model in MODELS_TO_MIGRATE:
            if is_migrated(db, model):
                HashMigrationTracker.set_migrated(model)
                logger.info(f"{model.__name__} is already fully migrated.")

        # migrate remaining models
        for model in MODELS_TO_MIGRATE:
            if not HashMigrationTracker.is_migrated(model):
                migrate_table(db, model)


def is_migrated(db: Session, model: Any) -> bool:  # type: ignore
    """
    Checks the database to see if there exists at least one unmigrated row.
    """

    query = text(
        f"SELECT EXISTS (SELECT 1 FROM {model.__tablename__} WHERE is_hash_migrated = false)"  # ignore: attr-defined
    )
    result = db.execute(query).scalar()
    return not result


def migrate_table(db: Session, model: Any, batch_size: int = 1000) -> None:
    """
    Migrate all unmigrated rows in the table corresponding to the passed in model.
    """

    while True:
        unmigrated_batch = (
            db.query(model)
            .filter(model.is_hash_migrated.is_(False))  # type:ignore[attr-defined]
            .limit(batch_size)
            .all()
        )
        if not unmigrated_batch:
            break

        for item in unmigrated_batch:
            item.migrate_hashed_fields()

        # commit after each batch is complete
        db.commit()

    HashMigrationTracker.set_migrated(model)
    logger.info(
        f"Completed hash migration for {model.__name__}."  # type:ignore[attr-defined]
    )
