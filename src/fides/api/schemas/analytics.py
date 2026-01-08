from enum import Enum, StrEnum


class Event(StrEnum):
    """Enum to hold analytics event names"""

    server_start = "server_start"
    endpoint_call = "endpoint_call"


class ExtraData(StrEnum):
    """Enum to hold keys for extra data"""

    fides_source = "fides_source"
