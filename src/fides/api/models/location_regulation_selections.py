from __future__ import annotations

from typing import Any, Dict, Iterable, Set

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Column,
    String,
    UniqueConstraint,
    insert,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base, FidesBase


class LocationRegulationSelections(Base):
    """
    Persists application-wide location and regulation selections in the DB.

    This is a single-row table. The single record describes global, application-wide selections
    about enabled locations and regulations.
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "location_regulation_selections"

    selected_locations = Column(
        ARRAY(String),
        nullable=False,
        default={},
    )
    selected_regulations = Column(
        ARRAY(String),
        nullable=False,
        default={},
    )
    single_row = Column(
        Boolean,
        default=True,
        nullable=False,
        unique=True,
    )  # used to constrain table to one row

    CheckConstraint("single_row", name="single_row_check")
    UniqueConstraint("single_row", name="single_row_unique")

    @classmethod
    def create_or_update(  # type: ignore[override]
        cls,
        db: Session,
        *,
        data: Dict[str, Any],
    ) -> FidesBase:
        """
        Creates the selections record if none exists, or updates the existing record.

        Here we effectively prevent more than a single record in the table.
        """
        existing_record = db.query(cls).first()
        if existing_record:
            updated_record = existing_record.update(
                db=db,
                data=data,
            )  # type: ignore[arg-type]
            return updated_record

        return cls.create(db=db, data=data)

    @classmethod
    async def create_or_update_async(
        cls,
        async_session: AsyncSession,
        *,
        data: Dict[str, Any],
    ) -> LocationRegulationSelections:
        """
        Creates the selections record if none exists, or updates the existing record.

        Here we effectively prevent more than a single record in the table.
        """
        async with async_session.begin():
            result = await async_session.execute(select(cls))  # type: ignore[arg-type]
            existing_record = result.scalars().first()
            if existing_record:
                await async_session.execute(
                    update(cls).where(cls.id == existing_record.id).values(data)  # type: ignore[arg-type]
                )
            else:
                await async_session.execute(insert(cls).values(data))  # type: ignore[arg-type]
            result = await async_session.execute(select(cls))  # type: ignore[arg-type]
            return result.scalars().first()

    @classmethod
    def set_selected_locations(
        cls,
        db: Session,
        selected_locations: Iterable[str],
    ) -> None:
        """Utility method to set the selected locations"""
        cls.create_or_update(db, data={"selected_locations": set(selected_locations)})

    @classmethod
    async def set_selected_locations_async(
        cls,
        async_session: AsyncSession,
        selected_locations: Iterable[str],
    ) -> None:
        """Utility method to set the selected locations"""
        await cls.create_or_update_async(
            async_session, data={"selected_locations": set(selected_locations)}
        )

    @classmethod
    def get_selected_locations(
        cls,
        db: Session,
    ) -> Set[str]:
        """
        Utility method to get the selected_locations, returned as a Set.
        """
        record = db.query(cls).first()
        if record:
            return set(record.selected_locations)
        return set()

    @classmethod
    async def get_selected_locations_async(
        cls,
        async_session: AsyncSession,
    ) -> Set[str]:
        """
        Utility method to get the selected_locations, returned as a Set.
        """
        async with async_session.begin():
            results = await async_session.execute(select(cls))  # type: ignore[arg-type]
            record = results.scalars().first()
            if record:
                return set(record.selected_locations)
            return set()

    @classmethod
    def set_selected_regulations(
        cls,
        db: Session,
        selected_regulations: Iterable[str],
    ) -> None:
        """Utility method to set the selected regulations"""
        cls.create_or_update(
            db, data={"selected_regulations": set(selected_regulations)}
        )

    @classmethod
    async def set_selected_regulations_async(
        cls,
        async_session: AsyncSession,
        selected_regulations: Iterable[str],
    ) -> None:
        """Utility method to set the selected regulations"""
        await cls.create_or_update_async(
            async_session, data={"selected_regulations": set(selected_regulations)}
        )

    @classmethod
    def get_selected_regulations(
        cls,
        db: Session,
    ) -> Set[str]:
        """
        Utility method to get the selected_regulations, returned as a Set.
        """
        record = db.query(cls).first()
        if record:
            return set(record.selected_regulations)
        return set()

    @classmethod
    async def get_selected_regulations_async(
        cls,
        async_session: AsyncSession,
    ) -> Set[str]:
        """
        Utility method to get the selected_regulations, returned as a Set.
        """
        async with async_session.begin():
            results = await async_session.execute(select(cls))  # type: ignore[arg-type]
            record = results.scalars().first()
            if record:
                return set(record.selected_regulations)
            return set()
