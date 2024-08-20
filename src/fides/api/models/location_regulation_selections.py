from __future__ import annotations

from collections import defaultdict
from enum import Enum
from functools import lru_cache
from os.path import dirname, join
from typing import Any, Dict, Iterable, List, Set, Union

import yaml
from pydantic import BaseModel
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
from fides.config.helpers import load_file

LOCATIONS_YAML_FILE_PATH = join(
    dirname(__file__),
    "../../data",
    "location",
    "locations.yml",
)


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
    selected_location_groups = (
        Column(  # Don't save this directly, it is saved as a side-effect of locations
            ARRAY(String),
            nullable=False,
            default={},
        )
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
        """Utility method to set the selected locations

        Calculates "location groups" from locations and saves this too. Since an allowed region on a Privacy Experience
        can be a location or a location group, precalculating location groups will make this a faster lookup.
        """
        selected_location_groups: Set[str] = group_locations_into_location_groups(
            selected_locations
        )

        cls.create_or_update(
            db,
            data={
                "selected_locations": set(selected_locations),
                "selected_location_groups": selected_location_groups,
            },
        )

    @classmethod
    async def set_selected_locations_async(
        cls,
        async_session: AsyncSession,
        selected_locations: Iterable[str],
    ) -> None:
        """Utility method to set the selected locations.  Location groups are calculated from locations and saved
        here as well"""
        selected_location_groups: Set[str] = group_locations_into_location_groups(
            selected_locations
        )

        await cls.create_or_update_async(
            async_session,
            data={
                "selected_locations": set(selected_locations),
                "selected_location_groups": selected_location_groups,
            },
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
    def get_selected_location_groups(
        cls,
        db: Session,
    ) -> Set[str]:
        """
        Utility method to get the selected_locations_groups, returned as a Set.

        Location Groups aren't saved directly, but as a side-effect of saving locations
        """
        record = db.query(cls).first()
        if record:
            return set(record.selected_location_groups)
        return set()

    @classmethod
    async def get_selected_location_groups_async(
        cls,
        async_session: AsyncSession,
    ) -> Set[str]:
        """
        Utility method to get the selected_location_groups, returned as a Set.

        Location Groups aren't saved directly, but as a side-effect of saving locations
        """
        async with async_session.begin():
            results = await async_session.execute(select(cls))  # type: ignore[arg-type]
            record = results.scalars().first()
            if record:
                return set(record.selected_location_groups)
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


def group_locations_into_location_groups(saved_locations: Iterable[str]) -> Set[str]:
    """Combines saved Locations into Location groups if applicable
    All Locations must be present for a Location Group to be valid.
    """
    saved_location_groups: List[str] = []

    for location_group, mapped_locations in location_group_to_location.items():
        if mapped_locations.issubset(saved_locations):
            saved_location_groups.append(location_group)

    return set(saved_location_groups)


class Continent(Enum):
    """Enum of supported continents"""

    north_america = "North America"
    south_america = "South America"
    asia = "Asia"
    africa = "Africa"
    oceania = "Oceania"
    europe = "Europe"


class Selection(BaseModel):
    """Selection schema"""

    id: str
    selected: bool = False


class LocationRegulationBase(Selection):
    """Base Location Regulation Schema"""

    name: str
    continent: Continent
    default_selected: bool = False


class Location(LocationRegulationBase):
    """Location schema"""

    belongs_to: List[str] = []
    regulation: List[str] = []


class LocationGroup(Location):
    """
    Location Group schema, currently the same as a location
    """


@lru_cache(maxsize=1)
def load_locations() -> Dict[str, Location]:
    """Loads location dict based on yml file on disk"""
    with open(load_file([LOCATIONS_YAML_FILE_PATH]), "r", encoding="utf-8") as file:
        _locations = yaml.safe_load(file).get("locations", [])
        location_dict = {}
        for location in _locations:
            location_dict[location["id"]] = Location.model_validate(location)
        return location_dict


@lru_cache(maxsize=1)
def load_location_groups() -> Dict[str, LocationGroup]:
    """Loads location_groups dict based on yml file on disk"""
    with open(load_file([LOCATIONS_YAML_FILE_PATH]), "r", encoding="utf-8") as file:
        _location_groups = yaml.safe_load(file).get("location_groups", [])
        location_group_dict = {}
        for location_group in _location_groups:
            location_group_dict[location_group["id"]] = LocationGroup.model_validate(
                location_group
            )
        return location_group_dict


@lru_cache(maxsize=1)
def load_location_group_to_location() -> Dict[str, Set[str]]:
    """Returns a mapping of locations to location groups

    This is helpful when locations are saved, for use in mapping those locations to location groups.
    Our current API only supports locations being saved directly.
    """
    location_ids_mapped_to_location: Dict[str, Location] = load_locations()

    location_groups_to_location_set: Dict[str, Set[str]] = defaultdict(set)

    for location in location_ids_mapped_to_location.values():
        if not location.belongs_to:
            continue

        for belongs_to in location.belongs_to:
            location_groups_to_location_set[belongs_to].add(location.id)

    return location_groups_to_location_set


@lru_cache(maxsize=1)
def load_regulations() -> Dict[str, LocationRegulationBase]:
    """Loads regulations dict based on yml file on disk"""
    with open(load_file([LOCATIONS_YAML_FILE_PATH]), "r", encoding="utf-8") as file:
        _regulations = yaml.safe_load(file).get("regulations", [])
        regulation_dict = {}
        for regulation in _regulations:
            regulation_dict[regulation["id"]] = LocationRegulationBase.model_validate(
                regulation
            )
        return regulation_dict


locations_by_id: Dict[str, Location] = (
    load_locations()
)  # should only be accessed for read-only access
location_groups: Dict[str, LocationGroup] = (
    load_location_groups()
)  # should only be accessed for read-only access
location_group_to_location: Dict[str, Set[str]] = (
    load_location_group_to_location()
)  # should only be accessed for read-only access
default_selected_locations: Set[str] = {
    id for id, location in locations_by_id.items() if location.default_selected
}


def _load_privacy_notice_regions() -> Dict[str, Union[Location, LocationGroup]]:
    """Merge Location dictionary with LocationGroup Dictionary"""
    return {**locations_by_id, **location_groups}


privacy_notice_regions_by_id: Dict[str, Union[Location, LocationGroup]] = (
    _load_privacy_notice_regions()
)  # should only be accessed for read-only access


# dynamically create an enum based on definitions loaded from YAML
# This is a combination of "locations" and "location groups" for use on Privacy Experiences
PrivacyNoticeRegion: Enum = Enum(  # type: ignore[misc]
    "PrivacyNoticeRegion",
    {location.id: location.id for location in privacy_notice_regions_by_id.values()},
)

# Create a notice region enum that includes regions we no longer support but still preserve
# on historical records for auditing purposes
deprecated_gb_regions = ["gb_eng", "gb_sct", "gb_wls", "gb_nir"]
current_regions = {
    location.id: location.id for location in privacy_notice_regions_by_id.values()
}
current_regions.update({gb_region: gb_region for gb_region in deprecated_gb_regions})
DeprecatedNoticeRegion: Enum = Enum(  # type: ignore[misc]
    "DeprecatedNoticeRegion", current_regions
)


def filter_regions_by_location(
    db: Session,
    regions: List[PrivacyNoticeRegion],
) -> List[PrivacyNoticeRegion]:
    """Filter a list of PrivacyNoticeRegions to only ones that match at the configured Location or
    LocationGroup level.

    Only Experiences with these regions will be shown to the end-user!
    """

    saved_locations: Set[str] = LocationRegulationSelections.get_selected_locations(db)
    saved_location_groups: Set[str] = (
        LocationRegulationSelections.get_selected_location_groups(db)
    )
    multilevel_locations: Set[str] = saved_locations.union(saved_location_groups)

    # For backwards-compatibility, if no system-wide locations or location groups are set,
    # all PrivacyNoticeRegions are available for use on Experiences
    if not multilevel_locations:
        return regions  # type: ignore[attr-defined]

    return [region for region in regions if region.value in multilevel_locations]
