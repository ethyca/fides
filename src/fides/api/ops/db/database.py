"""
Contains all of the logic for spinning up/tearing down the database.
"""
from alembic import command
from alembic.migration import MigrationContext
from fideslib.db.session import get_db_engine
from pydantic import PostgresDsn

from fides.api.ops.db.base import Base


def check_missing_migrations(database_url: PostgresDsn) -> None:
    """
    Tries to autogenerate migrations, returns True if a migration
    was generated.
    """

    engine = get_db_engine(database_uri=database_url)
    connection = engine.connect()

    migration_context = MigrationContext.configure(connection)
    result = command.autogen.compare_metadata(migration_context, Base.metadata)  # type: ignore

    if result:
        raise SystemExit("Migrations needs to be generated!")
    print("No migrations need to be generated.")
