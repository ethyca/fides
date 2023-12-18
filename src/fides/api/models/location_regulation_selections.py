from __future__ import annotations

from typing import Any, Dict, Iterable, Set

from sqlalchemy import ARRAY, Boolean, CheckConstraint, Column, String
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class LocationRegulationSelections(Base):
    """
    Persists application-wide location and regulation selections in the DB.

    This is a single-row table. The single record describes global, application-wide selections
    about enabled locations and regulations.
    """

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
        Boolean, default=True, nullable=False
    )  # used to constrain table to one row

    CheckConstraint("single_row", name="single_row_check")

    @classmethod
    def create_or_update(  # type: ignore[override]
        cls,
        db: Session,
        *,
        data: Dict[str, Any],
    ) -> LocationRegulationSelections:
        """
        Creates the selections record if none exists, or updates the existing record.

        Here we effectively prevent more than a single record in the table.
        """
        existing_record = db.query(cls).first()
        if existing_record:
            updated_record = existing_record.update(
                db=db,
                data=data,
            )
            return updated_record

        return cls.create(db=db, data=data)

    @classmethod
    def set_selected_locations(
        cls,
        db: Session,
        selected_locations: Iterable[str],
    ) -> LocationRegulationSelections:
        """Utility method to set the selected locations"""
        cls.create_or_update(db, data={"selected_locations": set(selected_locations)})

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
    def set_selected_regulations(
        cls,
        db: Session,
        selected_regulations: Iterable[str],
    ) -> LocationRegulationSelections:
        """Utility method to set the selected regulations"""
        cls.create_or_update(
            db, data={"selected_regulations": set(selected_regulations)}
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
