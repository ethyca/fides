"""
Contains all of the logic related to the database including connections, setup, teardown, etc.
"""
from os import path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from loguru import logger as log
from sqlalchemy_utils.functions import create_database, database_exists

from fidesapi.sql_models import SqlAlchemyBase, sql_model_map
from fidesapi.utils.errors import AlreadyExistsError, QueryError
from fidesctl.core.utils import get_db_engine
from fideslang import DEFAULT_TAXONOMY

from .crud import create_resource, upsert_resources


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
    await load_default_taxonomy()


def create_db_if_not_exists(database_url: str) -> None:
    """
    Creates a database which does not exist already.
    """
    if not database_exists(database_url):
        create_database(database_url)


async def load_default_taxonomy() -> None:
    """
    Attempts to insert organization resources into the database,
    to avoid overwriting a user-created organization under the
    `default_organization` fides_key.

    Upserts the remaining default taxonomy resources.
    """

    log.info("Loading the default fideslang taxonomy...")

    log.info("Processing organization resources...")
    organizations = list(map(dict, DEFAULT_TAXONOMY.dict()["organization"]))
    inserted = 0
    for org in organizations:
        try:
            await create_resource(sql_model_map["organization"], org)
            inserted += 1
        except AlreadyExistsError:
            pass

    log.info(f"INSERTED {inserted} organization resource(s)")
    log.info(f"SKIPPED {len(organizations)-inserted} organization resource(s)")

    upsert_resource_types = list(DEFAULT_TAXONOMY.__fields_set__)
    upsert_resource_types.remove("organization")

    log.info("UPSERTING the remaining default fideslang taxonomy resources")
    for resource_type in upsert_resource_types:
        log.info(f"Processing {resource_type} resources...")
        resources = list(map(dict, DEFAULT_TAXONOMY.dict()[resource_type]))

        try:
            result = await upsert_resources(sql_model_map[resource_type], resources)
        except QueryError:
            pass  # The upsert_resources function will log the error
        else:
            log.info(f"INSERTED {result[0]} {resource_type} resource(s)")
            log.info(f"UPDATED {result[1]} {resource_type} resource(s)")


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
