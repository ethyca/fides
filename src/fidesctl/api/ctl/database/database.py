"""
Contains all of the logic related to the database including connections, setup, teardown, etc.
"""
from os import path

from alembic import command, script
from alembic.config import Config
from alembic.runtime import migration
from fideslang import DEFAULT_TAXONOMY
from fideslib.db.base import Base
from loguru import logger as log
from sqlalchemy import create_engine
from sqlalchemy_utils.functions import create_database, database_exists

from fidesctl.api.ctl.sql_models import sql_model_map
from fidesctl.api.ctl.utils.errors import (
    AlreadyExistsError,
    QueryError,
    get_full_exception_name,
)
from fidesctl.ctl.core.utils import get_db_engine

from .crud import create_resource, list_resource


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

    log.info("INSERTING new default fideslang taxonomy resources")
    for resource_type in upsert_resource_types:
        log.info(f"Processing {resource_type} resources...")
        default_resources = DEFAULT_TAXONOMY.dict()[resource_type]
        existing_resources = await list_resource(sql_model_map[resource_type])
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
                await create_resource(sql_model_map[resource_type], resource)
        except QueryError:
            pass  # The create_resource function will log the error
        else:
            log.info(f"INSERTED {len(resources)} {resource_type} resource(s)")


def reset_db(database_url: str) -> None:
    """
    Drops all tables/metadata from the database.
    """
    log.info("Resetting database")
    engine = get_db_engine(database_url)
    connection = engine.connect()
    Base.metadata.drop_all(connection)

    migration_context = migration.MigrationContext.configure(connection)
    version = migration_context._version  # pylint: disable=protected-access
    if version.exists(connection):
        version.drop(connection)


def get_db_health(database_url: str) -> str:
    """Checks if the db is reachable and up to date in alembic migrations"""
    try:
        engine = create_engine(database_url)
        alembic_config = get_alembic_config(database_url)
        alembic_script_directory = script.ScriptDirectory.from_config(alembic_config)
        with engine.begin() as conn:
            context = migration.MigrationContext.configure(conn)
            if (
                context.get_current_revision()
                != alembic_script_directory.get_current_head()
            ):
                return "needs migration"
        return "healthy"
    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error(f"Unable to reach the database: {error_type}: {error}")
        return "unhealthy"


async def configure_db(database_url: str) -> None:
    "Set up the db to be used by the app."
    try:
        create_db_if_not_exists(database_url)
        await init_db(database_url)
    except Exception as error:  # pylint: disable=broad-except
        error_type = get_full_exception_name(error)
        log.error(f"Unable to configure database: {error_type}: {error}")
