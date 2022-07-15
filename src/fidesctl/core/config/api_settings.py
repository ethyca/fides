"""This module handles finding and parsing fides configuration files."""

# pylint: disable=C0115,C0116, E0213
from .fides_settings import FidesSettings


class APISettings(FidesSettings):
    """Class used to store values from the 'cli' section of the config."""
