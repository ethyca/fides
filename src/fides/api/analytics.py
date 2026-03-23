import os
from typing import Optional


def in_docker_container() -> bool:
    """`True` if the command was submitted within a Docker container. Default: `False`."""
    return bool(os.getenv("RUNNING_IN_DOCKER") == "true")


def accessed_through_local_host(hostname: Optional[str]) -> bool:
    """`True`if the event was submitted through a local host, e,g, 127.0.0.1."""
    LOCAL_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "testserver"]
    return hostname in LOCAL_HOSTS
