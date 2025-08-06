"""
Utility functions for handling location data and converting location codes to display names.
"""

from functools import lru_cache
from typing import Dict

from fides.api.models.location_regulation_selections import (
    load_location_groups,
    load_locations,
)

# Manual mapping for special cases and common subdivision codes
SUBDIVISION_DISPLAY_NAMES: Dict[str, str] = {
    # United States states
    "US-AL": "Alabama",
    "US-AK": "Alaska",
    "US-AZ": "Arizona",
    "US-AR": "Arkansas",
    "US-CA": "California",
    "US-CO": "Colorado",
    "US-CT": "Connecticut",
    "US-DE": "Delaware",
    "US-FL": "Florida",
    "US-GA": "Georgia",
    "US-HI": "Hawaii",
    "US-ID": "Idaho",
    "US-IL": "Illinois",
    "US-IN": "Indiana",
    "US-IA": "Iowa",
    "US-KS": "Kansas",
    "US-KY": "Kentucky",
    "US-LA": "Louisiana",
    "US-ME": "Maine",
    "US-MD": "Maryland",
    "US-MA": "Massachusetts",
    "US-MI": "Michigan",
    "US-MN": "Minnesota",
    "US-MS": "Mississippi",
    "US-MO": "Missouri",
    "US-MT": "Montana",
    "US-NE": "Nebraska",
    "US-NV": "Nevada",
    "US-NH": "New Hampshire",
    "US-NJ": "New Jersey",
    "US-NM": "New Mexico",
    "US-NY": "New York",
    "US-NC": "North Carolina",
    "US-ND": "North Dakota",
    "US-OH": "Ohio",
    "US-OK": "Oklahoma",
    "US-OR": "Oregon",
    "US-PA": "Pennsylvania",
    "US-RI": "Rhode Island",
    "US-SC": "South Carolina",
    "US-SD": "South Dakota",
    "US-TN": "Tennessee",
    "US-TX": "Texas",
    "US-UT": "Utah",
    "US-VT": "Vermont",
    "US-VA": "Virginia",
    "US-WA": "Washington",
    "US-WV": "West Virginia",
    "US-WI": "Wisconsin",
    "US-WY": "Wyoming",
    # Canadian provinces and territories
    "CA-AB": "Alberta",
    "CA-BC": "British Columbia",
    "CA-MB": "Manitoba",
    "CA-NB": "New Brunswick",
    "CA-NL": "Newfoundland and Labrador",
    "CA-NS": "Nova Scotia",
    "CA-ON": "Ontario",
    "CA-PE": "Prince Edward Island",
    "CA-QC": "Quebec",
    "CA-SK": "Saskatchewan",
    "CA-NT": "Northwest Territories",
    "CA-NU": "Nunavut",
    "CA-YT": "Yukon",
    # UK constituent countries
    "GB-ENG": "England",
    "GB-SCT": "Scotland",
    "GB-WAL": "Wales",
    "GB-NIR": "Northern Ireland",
    # Special case
    "EEA": "European Economic Area",
}


@lru_cache(maxsize=1)
def get_country_display_names() -> Dict[str, str]:
    """Load country display names from the locations.yml file."""
    country_names = {}

    # Load from both locations and location_groups
    locations = load_locations()
    location_groups = load_location_groups()

    # Check locations first
    for location_id, location in locations.items():
        if location.is_country:
            country_names[location_id.upper()] = location.name

    # Check location_groups for additional countries
    for location_id, location in location_groups.items():
        if location.is_country:
            country_names[location_id.upper()] = location.name

    return country_names


def convert_location_to_display_name(location_code: str) -> str:
    """
    Convert an ISO 3166 location code to a human-readable display name.

    Args:
        location_code: ISO 3166-1 alpha-2 country code or ISO 3166-2 subdivision code
                      (e.g., "US", "US-CA", "GB", "CA-ON", "EEA")

    Returns:
        Human-readable display name

    Examples:
        "US" -> "United States"
        "US-CA" -> "United States (California)"
        "GB" -> "United Kingdom"
        "CA-ON" -> "Canada (Ontario)"
        "EEA" -> "European Economic Area"
    """
    location_code = location_code.upper()

    # Handle special EEA code
    if location_code == "EEA":
        return SUBDIVISION_DISPLAY_NAMES["EEA"]

    # Handle special UK subdivision codes that are complete replacements (like GB-ENG -> "England")
    uk_special_cases = ["GB-ENG", "GB-SCT", "GB-WAL", "GB-NIR"]
    if location_code in uk_special_cases and location_code in SUBDIVISION_DISPLAY_NAMES:
        return SUBDIVISION_DISPLAY_NAMES[location_code]

    # Handle subdivision codes (e.g., "US-CA")
    if "-" in location_code:
        country_code, subdivision_code = location_code.split("-", 1)

        # Get country name
        country_names = get_country_display_names()
        country_name = country_names.get(country_code)

        if country_name:
            # Check if we have a specific subdivision name
            full_code = f"{country_code}-{subdivision_code}"
            if full_code in SUBDIVISION_DISPLAY_NAMES:
                subdivision_name = SUBDIVISION_DISPLAY_NAMES[full_code]
                return f"{country_name} ({subdivision_name})"
            # Fallback to just showing the subdivision code
            return f"{country_name} ({subdivision_code})"

        # Unknown country code
        return location_code

    # Handle country codes (e.g., "US")
    country_names = get_country_display_names()
    return country_names.get(location_code, location_code)
