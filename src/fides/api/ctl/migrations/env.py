from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from fidesctl.api.ctl.utils.logger import setup as setup_fidesapi_logger
from fidesctl.ctl.core.config import get_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
alembic_config = context.config
fidesctl_config = get_config()

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(alembic_config.config_file_name)
setup_fidesapi_logger(
    fidesctl_config.logging.level,
    serialize=fidesctl_config.logging.serialization,
    desination=fidesctl_config.logging.destination,
)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from fidesctl.api.ctl.sql_models import Base

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = fidesctl_config.database.sync_database_uri
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = alembic_config.get_section(alembic_config.config_ini_section)
    configuration["sqlalchemy.url"] = fidesctl_config.database.sync_database_uri
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
