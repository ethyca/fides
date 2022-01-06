"""Set up async db sessions"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fidesctl.core.config.config import get_config


config = get_config()
engine = create_async_engine(
    config.api.database_url,
    echo=False,
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
