from enum import Enum


class EVENT(str, Enum):
    """Enum to hold analytics event names"""

    server_start = "server_start"
