"""
Contains all of the logic related to the database including connections, setup, teardown, etc.
"""

from os import path
from typing import Literal, Optional, Tuple

from alembic import command, script
from alembic.config import Config
from alembic.runtime import migration
from loguru import logger as log
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists
from sqlalchemy_utils.types.encrypted.encrypted_type import InvalidCiphertextError

from fides.api.db.base import Base  # type: ignore[attr-defined]
from fides.api.db.seed import load_default_resources
from fides.api.db.session import get_db_engine
from fides.api.util.errors import get_full_exception_name

DatabaseHealth = Literal["healthy", "unhealthy", "needs migration"]


def get_alembic_config(database_url: str) -> Config:
    """
    Do lots of magic to make alembic work programmatically from the CLI.
    """

    migrations_dir = path.dirname(path.abspath(__file__))
    directory = path.join(migrations_dir, "../alembic/migrations")
    config = Config(path.join(migrations_dir, "../alembic/alembic.ini"))
    config.set_main_option("script_location", directory.replace("%", "%%"))
    # Avoids invalid interpolation syntax errors if % in string
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def upgrade_db(alembic_config: Config, revision: str = "head") -> None:
    """Upgrade the database to the specified migration revision."""
    log.info(f"Running database upgrade to revision {revision}")
    command.upgrade(alembic_config, revision)


def init_db(database_url: str) -> None:
    """
    Runs the migrations and creates all of the database objects.
    """
    alembic_config = get_alembic_config(database_url)
    upgrade_db(alembic_config)


def downgrade_db(alembic_config: Config, revision: str = "head") -> None:
    """Downgrade the database to the specified migration revision."""
    log.info(f"Running database downgrade to revision {revision}")
    command.downgrade(alembic_config, revision)


def migrate_db(
    database_url: str,
    revision: str = "head",
    downgrade: bool = False,
) -> None:
    """
    Runs migrations and creates database objects if needed.

    Safe to run on an existing database when upgrading Fides version.
    """
    log.info("Migrating database")
    alembic_config = get_alembic_config(database_url)
    if downgrade:
        downgrade_db(alembic_config, revision)
    else:
        upgrade_db(alembic_config, revision)


def create_db_if_not_exists(database_url: str) -> None:
    """
    Creates a database which does not exist already.
    """
    if not database_exists(database_url):
        create_database(database_url)


def reset_db(database_url: str) -> None:
    """
    Drops all tables/metadata from the database.
    """
    log.info("Resetting database...")
    engine = get_db_engine(database_uri=database_url)
    with engine.connect() as connection:
        log.info("Dropping tables...")
        Base.metadata.drop_all(connection)

        log.info("Dropping Alembic table...")
        migration_context = migration.MigrationContext.configure(connection)
        version = migration_context._version  # pylint: disable=protected-access
        if version.exists(connection):
            version.drop(connection)
    log.info("Reset complete.")


def get_db_health(
    database_url: str, db: Session
) -> Tuple[DatabaseHealth, Optional[str]]:
    """Checks if the db is reachable and up-to-date with Alembic migrations."""
    try:
        alembic_config = get_alembic_config(database_url)
        alembic_script_directory = script.ScriptDirectory.from_config(alembic_config)
        context = migration.MigrationContext.configure(db.connection())
        current_revision = context.get_current_revision()
        if (
            context.get_current_revision()
            != alembic_script_directory.get_current_head()
        ):
            db_health: DatabaseHealth = "needs migration"
        else:
            db_health = "healthy"
        return db_health, current_revision
    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error("Unable to reach the database: {}: {}", error_type, error)
        return ("unhealthy", None)


def seed_db(session: Session) -> None:
    """Load default resources into the database"""
    load_default_resources(session)


def configure_db(database_url: str, revision: Optional[str] = "head") -> None:
    """Set up the db to be used by the app. Creates db if needed and runs migrations."""
    try:
        create_db_if_not_exists(database_url)
        migrate_db(database_url, revision=revision)  # type: ignore[arg-type]

    except InvalidCiphertextError as cipher_error:
        log.error(
            "Unable to configure database due to a decryption error! Check to ensure your `app_encryption_key` has not changed."
        )
        log.opt(exception=True).error(cipher_error)

    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error("Unable to configure database: {}: {}", error_type, error)
        log.opt(exception=True).error(error)
        raise


def check_missing_migrations(database_url: str) -> None:
    """
    Tries to autogenerate migrations, returns True if a migration
    was generated.
    """

    engine = get_db_engine(database_uri=database_url)
    connection = engine.connect()

    migration_context = migration.MigrationContext.configure(connection)
    result = command.autogen.compare_metadata(migration_context, Base.metadata)  # type: ignore[attr-defined]

    if result:
        raise SystemExit("Migrations needs to be generated!")
    print("No migrations need to be generated.")
