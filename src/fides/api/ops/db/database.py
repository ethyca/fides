"""
Contains all of the logic for spinning up/tearing down the database.
"""
from os import path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from fideslib.db.session import get_db_engine
from pydantic import PostgresDsn

from .base import Base


def get_alembic_config(database_url: str) -> Config:
    """
    Do lots of magic to make alembic work programmatically.
    """

    current_dir = path.dirname(path.abspath(__file__))
    migrations_dir = path.abspath(path.join(current_dir, "../migrations"))

    alembic_config = Config(path.abspath(path.join(current_dir, "../alembic.ini")))
    alembic_config.set_main_option("script_location", migrations_dir.replace("%", "%%"))
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    return alembic_config


def upgrade_db(alembic_config: Config, revision: str = "head") -> None:
    "Upgrade the database to the specified migration revision."

    command.upgrade(alembic_config, revision)


def init_db(database_url: PostgresDsn) -> None:
    """
    Runs the migrations and creates all of the database objects.
    """
    alembic_config = get_alembic_config(database_url)
    upgrade_db(alembic_config)


def check_missing_migrations(database_url: PostgresDsn) -> None:
    """
    Tries to autogenerate migrations, returns True if a migration
    was generated.
    """

    engine = get_db_engine(database_uri=database_url)
    connection = engine.connect()

    migration_context = MigrationContext.configure(connection)
    result = command.autogen.compare_metadata(migration_context, Base.metadata)

    if result:
        raise SystemExit("Migrations needs to be generated!")
    print("No migrations need to be generated.")


def reset_db(database_url: PostgresDsn) -> None:
    """
    Drops all tables/metadata from the database.
    """
    engine = get_db_engine(database_uri=database_url)
    connection = engine.connect()
    Base.metadata.drop_all(connection)

    migration_context = MigrationContext.configure(connection)
    version = migration_context._version  # pylint: disable=protected-access
    if version.exists(connection):
        version.drop(connection)
