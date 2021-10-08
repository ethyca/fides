"""
Contains all of the logic for spinning up/tearing down the database.
"""
import os

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext

from fidesapi.sql_models import SqlAlchemyBase
from fidesctl.core.apply import apply
from fidesctl.core.config import FidesctlConfig
from fidesctl.core.utils import get_db_engine
from fideslang import DEFAULT_TAXONOMY


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

    command.upgrade(alembic_config, revision)


def init_db(database_url: str, fidesctl_config: FidesctlConfig) -> None:
    """
    Runs the migrations and creates all of the database objects.
    """
    alembic_config = get_alembic_config(database_url)
    upgrade_db(alembic_config)
    load_default_taxonomy(fidesctl_config)


def load_default_taxonomy(fidesctl_config: FidesctlConfig) -> None:
    "Loads the default taxonomy into the database."
    config = fidesctl_config
    apply(
        url=config.cli.server_url,
        taxonomy=DEFAULT_TAXONOMY,
        headers=config.user.request_headers,
    )


def reset_db(database_url: str) -> None:
    """
    Drops all tables/metadata from the database.
    """
    engine = get_db_engine(database_url)
    connection = engine.connect()
    SqlAlchemyBase.metadata.drop_all(connection)

    migration_context = MigrationContext.configure(connection)
    version = migration_context._version  # pylint: disable=protected-access
    if version.exists(connection):
        version.drop(connection)
