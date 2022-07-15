"""Set up async db sessions"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fidesctl.core.config import get_config

config = get_config()
engine = create_async_engine(
    config.database.async_database_uri,
    echo=False,
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
