import logging
import os
from platform import system
from typing import Optional

from fideslog.sdk.python.client import AnalyticsClient
from fideslog.sdk.python.event import AnalyticsEvent
from fideslog.sdk.python.exceptions import AnalyticsError

from fidesops import __version__ as fidesops_version
from fidesops.core.config import config

logger = logging.getLogger(__name__)


def in_docker_container() -> bool:
    """`True` if the command was submitted within a Docker container. Default: `False`."""
    return bool(os.getenv("RUNNING_IN_DOCKER") == "true")


def accessed_through_local_host(hostname: Optional[str]) -> bool:
    """`True`if the event was submitted through a local host, e,g, 127.0.0.1."""
    # testserver is hostname in unit tests
    LOCAL_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "testserver"]
    return hostname in LOCAL_HOSTS


analytics_client = AnalyticsClient(
    client_id=config.root_user.ANALYTICS_ID,
    developer_mode=config.dev_mode,
    extra_data=None,
    os=system(),
    product_name="fidesops",
    production_version=fidesops_version,
)


def send_analytics_event(event: AnalyticsEvent) -> None:
    if config.root_user.ANALYTICS_OPT_OUT:
        return
    try:
        analytics_client.send(event)
    except AnalyticsError as err:
        logger.warning(f"Error sending analytics event: {err}")
    else:
        logger.info(
            f"Analytics event sent: {event.event} with client id: {analytics_client.client_id}"
        )
