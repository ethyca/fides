from collections import defaultdict
from enum import Enum
from functools import lru_cache
from os.path import dirname, join
from typing import Dict, List, Set, Union

import yaml
from pydantic import BaseModel
from sqlalchemy.orm import Session

from fides.api.models.location_regulation_selections import LocationRegulationSelections
from fides.config.helpers import load_file

LOCATIONS_YAML_FILE_PATH = join(
    dirname(__file__),
    "../../data",
    "location",
    "locations.yml",
)


class Continent(Enum):
    north_america = "North America"
    south_america = "South America"
    asia = "Asia"
    africa = "Africa"
    oceania = "Oceania"
    europe = "Europe"


class Selection(BaseModel):
    id: str
    selected: bool = False


class LocationRegulationBase(Selection):
    name: str
    continent: Continent


class Location(LocationRegulationBase):
    belongs_to: List[str] = []
    regulation: List[str] = []


class LocationGroup(Location):
    """
    Used to represent location groups in API responses.
    """


@lru_cache(maxsize=1)
def load_locations() -> Dict[str, Location]:
    """Loads location dict based on yml file on disk"""
    with open(load_file([LOCATIONS_YAML_FILE_PATH]), "r", encoding="utf-8") as file:
        _locations = yaml.safe_load(file).get("locations", [])
        location_dict = {}
        for location in _locations:
            location_dict[location["id"]] = Location.parse_obj(location)
        return location_dict


@lru_cache(maxsize=1)
def load_location_groups() -> Dict[str, LocationGroup]:
    """Loads location_groups dict based on yml file on disk"""
    with open(load_file([LOCATIONS_YAML_FILE_PATH]), "r", encoding="utf-8") as file:
        _location_groups = yaml.safe_load(file).get("location_groups", [])
        location_group_dict = {}
        for location_group in _location_groups:
            location_group_dict[location_group["id"]] = LocationGroup.parse_obj(
                location_group
            )
        return location_group_dict


@lru_cache(maxsize=1)
def load_location_group_to_location() -> Dict[str, Set[str]]:
    """Returns a mapping of locations to location groups"""
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
            regulation_dict[regulation["id"]] = LocationRegulationBase.parse_obj(
                regulation
            )
        return regulation_dict


locations_by_id: Dict[
    str, Location
] = load_locations()  # should only be accessed for read-only access
location_groups: Dict[
    str, LocationGroup
] = load_location_groups()  # should only be accessed for read-only access
location_group_to_location: Dict[
    str, Set[str]
] = load_location_group_to_location()  # should only be accessed for read-only access


def _load_privacy_notice_regions() -> Dict[str, Union[Location, LocationGroup]]:
    """Merge Location dictionary with LocationGroup Dictionary"""
    return {**locations_by_id, **location_groups}


supported_locations_by_id: Dict[
    str, Union[Location, LocationGroup]
] = _load_privacy_notice_regions()  # should only be accessed for read-only access


# dynamically create an enum based on definitions loaded from YAML
PrivacyNoticeRegion: Enum = Enum(  # type: ignore[misc]
    "PrivacyNoticeRegion",
    {location.id: location.id for location in supported_locations_by_id.values()},
)


def filter_regions_by_location(
    db: Session,
    regions: List[PrivacyNoticeRegion],
) -> List[PrivacyNoticeRegion]:
    """Filter a list of PrivacyNoticeRegion to only ones that match at the configured Location or LocationGroup level.

    Locations are stored at the Location level while regions can be saved at the Location level
    or the Location group level.
    """

    locations: Set[str] = LocationRegulationSelections.get_selected_locations(db)

    if not locations:
        return regions  # type: ignore[attr-defined]

    filtered_regions: List[PrivacyNoticeRegion] = []

    for region in regions:
        # Explode any Location Groups to Locations so they can be compared against apples to apples
        # with locations
        expanded_regions: Set[str] = location_group_to_location.get(
            region.value, {region.value}
        )
        if expanded_regions.issubset(locations):
            filtered_regions.append(region)

    return filtered_regions
