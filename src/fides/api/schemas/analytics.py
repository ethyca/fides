from enum import Enum


class Event(str, Enum):
    """Enum to hold analytics event names"""

    server_start = "server_start"
    endpoint_call = "endpoint_call"


class ExtraData(str, Enum):
    """Enum to hold keys for extra data"""

    fides_source = "fides_source"
