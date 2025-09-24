from typing import Any, Optional

from sqlalchemy import Boolean, Column, String, insert, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base


class WebMonitorGroupJob(Base):
    """SQL model for storing data returned from a web monitor group job"""

    @declared_attr
    def __tablename__(self) -> str:
        return "web_monitor_group_job"

    # The id for the web monitor group on the web monitor service
    group_id = Column(String, nullable=False, unique=True)

    # The raw experiences data obtained for that group from the web monitor service
    raw_experiences_data = Column(JSONB, nullable=True)
    # The processed experiences data, used to calculate an StagedResource's consent status
    processed_experiences_data = Column(JSONB, nullable=True)

    # Whether this data is from a test_website monitor rather than a real one
    is_test_run = Column(Boolean, nullable=False, default=False)

    @classmethod
    async def create_async(
        cls,
        async_session: AsyncSession,
        *,
        group_id: str,
        is_test_run: Optional[bool] = False,
        raw_experiences_data: Optional[dict[str, Any]] = None,
        processed_experiences_data: Optional[dict[str, Any]] = None,
    ) -> "WebMonitorGroupJob":
        """Create a new WebMonitorGroupJob"""
        values = {
            "group_id": group_id,
            "is_test_run": is_test_run,
            "raw_experiences_data": raw_experiences_data,
            "processed_experiences_data": processed_experiences_data,
        }
        stmt = insert(cls.__table__).values(**values).returning(*cls.__table__.columns)
        result = await async_session.execute(stmt)
        row = result.first()
        return cls(**dict(row))

    @classmethod
    async def get_by_group_id_async(
        cls, async_session: AsyncSession, group_id: str
    ) -> Optional["WebMonitorGroupJob"]:
        """Get a WebMonitorGroupJob by group_id"""
        stmt = select(*cls.__table__.columns).where(
            cls.__table__.c.group_id == group_id
        )
        result = await async_session.execute(stmt)
        row = result.first()
        return cls(**dict(row)) if row else None
