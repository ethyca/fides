"""
Contains all of the logic related to the database including connections, setup, teardown, etc.
"""
from os import path

from alembic import command, script
from alembic.config import Config
from alembic.runtime import migration
from loguru import logger as log
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists
from sqlalchemy_utils.types.encrypted.encrypted_type import InvalidCiphertextError

from fides.api.ctl.utils.errors import get_full_exception_name
from fides.core.config import get_config
from fides.core.utils import get_db_engine
from fides.lib.db.base import Base  # type: ignore[attr-defined]

from .seed import load_default_resources

CONFIG = get_config()


def get_alembic_config(database_url: str) -> Config:
    """
    Do lots of magic to make alembic work programmatically from the CLI.
    """

    migrations_dir = path.dirname(path.abspath(__file__))
    directory = path.join(migrations_dir, "../migrations")
    config = Config(path.join(migrations_dir, "../alembic.ini"))
    config.set_main_option("script_location", directory.replace("%", "%%"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade_db(alembic_config: Config, revision: str = "head") -> None:
    "Upgrade the database to the specified migration revision."
    log.info("Running database migrations")
    command.upgrade(alembic_config, revision)


async def init_db(database_url: str) -> None:
    """
    Runs the migrations and creates all of the database objects.
    """
    log.info("Initializing database")
    alembic_config = get_alembic_config(database_url)
    upgrade_db(alembic_config)
    await load_default_resources()


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
    engine = get_db_engine(database_url)
    with engine.connect() as connection:
        log.info("Dropping tables...")
        Base.metadata.drop_all(connection)

        log.info("Dropping Alembic table...")
        migration_context = migration.MigrationContext.configure(connection)
        version = migration_context._version  # pylint: disable=protected-access
        if version.exists(connection):
            version.drop(connection)
    log.info("Reset complete.")


def get_db_health(database_url: str, db: Session) -> str:
    """Checks if the db is reachable and up to date in alembic migrations"""
    try:
        alembic_config = get_alembic_config(database_url)
        alembic_script_directory = script.ScriptDirectory.from_config(alembic_config)
        context = migration.MigrationContext.configure(db.connection())

        if (
            context.get_current_revision()
            != alembic_script_directory.get_current_head()
        ):
            return "needs migration"
        return "healthy"
    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error("Unable to reach the database: {}: {}", error_type, error)
        return "unhealthy"


async def configure_db(database_url: str) -> None:
    """Set up the db to be used by the app."""
    try:
        create_db_if_not_exists(database_url)
        await init_db(database_url)
    except InvalidCiphertextError as cipher_error:
        log.error(
            "Unable to configure database due to a decryption error! Check to ensure your `app_encryption_key` has not changed."
        )
        log.opt(exception=True).error(cipher_error)

    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error("Unable to configure database: {}: {}", error_type, error)
        log.opt(exception=True).error(error)
