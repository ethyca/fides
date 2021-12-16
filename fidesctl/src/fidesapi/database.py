"""
Contains all of the logic for spinning up/tearing down the database.
"""
import os

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from loguru import logger as log
from sqlalchemy_utils.functions import create_database, database_exists

from fidesapi.errors import QueryError
from fidesapi.sql_models import sql_model_map, SqlAlchemyBase
from fidesapi.crud import upsert_resources
from fideslang import DEFAULT_TAXONOMY
from fidesctl.core.utils import get_db_engine


def get_alembic_config(database_url: str) -> Config:
    """
    Do lots of magic to make alembic work programmatically from the CLI.
    """

    migrations_dir = os.path.dirname(os.path.abspath(__file__))
    directory = os.path.join(migrations_dir, "migrations")
    config = Config(os.path.join(migrations_dir, "alembic.ini"))
    config.set_main_option("script_location", directory.replace("%", "%%"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade_db(alembic_config: Config, revision: str = "head") -> None:
    "Upgrade the database to the specified migration revision."
    log.info("Running database migrations")
    command.upgrade(alembic_config, revision)


def init_db(database_url: str) -> None:
    """
    Runs the migrations and creates all of the database objects.
    """
    log.info("Initializing database")
    alembic_config = get_alembic_config(database_url)
    upgrade_db(alembic_config)
    load_default_taxonomy()


def create_db_if_not_exists(database_url: str) -> None:
    """
    Creates a database which does not exist already.
    """
    if not database_exists(database_url):
        create_database(database_url)


def load_default_taxonomy() -> None:
    "Upserts the default taxonomy into the database."
    log.info("UPSERTING the default fideslang taxonomy")
    for resource_type in list(DEFAULT_TAXONOMY.__fields_set__):
        log.info(f"Processing {resource_type} resources...")
        resources = list(map(dict, dict(DEFAULT_TAXONOMY)[resource_type]))

        try:
            upsert_resources(sql_model_map[resource_type], resources)
        except QueryError:
            pass  # The upsert_resources function will log the error
        else:
            log.info(
                f"Successfully UPSERTED {len(resources)} {resource_type} resources"
            )


def reset_db(database_url: str) -> None:
    """
    Drops all tables/metadata from the database.
    """
    log.info("Resetting database")
    engine = get_db_engine(database_url)
    connection = engine.connect()
    SqlAlchemyBase.metadata.drop_all(connection)

    migration_context = MigrationContext.configure(connection)
    version = migration_context._version  # pylint: disable=protected-access
    if version.exists(connection):
        version.drop(connection)
