from __future__ import with_statement

import os
import sys

# Add this file to the PYTHONPATH so we can import our base model
from typing import List

from sqlalchemy.sql.schema import SchemaItem

sys.path = ["", ".."] + sys.path[1:]

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# add your model's MetaData object here
# for 'autogenerate' support
from fidesops.core.config import config as fides_config
from fidesops.db.base import Base  # pylint: disable=W0611

# Load the correct environment
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """
    Returns a Fidesops database URL. If the environment is set to TESTING
    the URL will point at the test database.
    """

    database_uri = fides_config.database.SQLALCHEMY_DATABASE_URI
    if fides_config.is_test_mode:
        database_uri = fides_config.database.SQLALCHEMY_TEST_DATABASE_URI
    return database_uri


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,  # Lets alembic recognize that a server default has changed
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,  # Lets alembic recognize that a server default has changed
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
