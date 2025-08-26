import re

from anyascii import anyascii  # type: ignore

# Regex to validate a ISO 3166-2 code:
# 1. Starts with a 2 letter country code (e.g. "US", "GB") (see ISO 3166-1 alpha-2)
# 2. (Optional) Ends with a 1-3 alphanumeric character region code (e.g. "CA", "123", "X") (see ISO 3166-2)
# 3. Country & region codes must be separated by a hyphen (e.g. "US-CA")
#
# Fides also supports a special `EEA` geolocation code to denote the European
# Economic Area; this is not part of ISO 3166-2, but is supported for convenience.
VALID_ISO_3166_LOCATION_REGEX = re.compile(
    r"^(?:([a-z]{2})(-[a-z0-9]{1,3})?|(eea))$", re.IGNORECASE
)


def normalize_location_code(location: str) -> str:
    """
    Normalize a location code to ISO 3166-2 format.

    Converts location codes to the idiomatic format:
    - Uppercase (e.g., "us-ca" -> "US-CA")
    - Hyphens instead of underscores (e.g., "US_CA" -> "US-CA")
    - Supports special codes like "EEA"

    Args:
        location: Input location code (e.g., "us-ca", "US_NY", "gb", "eea")

    Returns:
        Normalized location code (e.g., "US-CA", "US-NY", "GB", "EEA")

    Raises:
        ValueError: If the normalized location doesn't match ISO 3166-2 format

    Examples:
        normalize_location_code("us-ca") -> "US-CA"
        normalize_location_code("US_NY") -> "US-NY"
        normalize_location_code("gb") -> "GB"
        normalize_location_code("eea") -> "EEA"
    """
    if not location:
        raise ValueError("Location code cannot be empty")

    # Convert to uppercase and replace underscores with hyphens
    normalized = location.upper().replace("_", "-")

    # Validate against ISO 3166-2 format
    if not VALID_ISO_3166_LOCATION_REGEX.match(normalized):
        raise ValueError(
            f"Invalid location format '{location}'. Must follow ISO 3166 format "
            "(e.g., 'US', 'US-CA', 'GB', 'CA-ON', 'EEA')"
        )

    return normalized


def to_snake_case(text: str) -> str:
    """
    Returns a snake-cased str based upon the input text.

    Examples:
        "foo bar" -> "foo_bar"
        "foo\nbar" -> "foo_bar"
        "foo\tbar" -> "foo_bar"
        "foo-bar" -> "foo_bar"
        "foo*bar" -> "foobar"
    """
    text = anyascii(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text
