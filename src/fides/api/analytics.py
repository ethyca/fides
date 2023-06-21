import os
from platform import system
from typing import Optional

from fideslog.sdk.python.client import AnalyticsClient
from fideslog.sdk.python.event import AnalyticsEvent
from fideslog.sdk.python.exceptions import AnalyticsError
from loguru import logger as log

from fides import __version__ as fides_version
from fides.api.models.registration import UserRegistration
from fides.config import CONFIG


def in_docker_container() -> bool:
    """`True` if the command was submitted within a Docker container. Default: `False`."""
    return bool(os.getenv("RUNNING_IN_DOCKER") == "true")


def accessed_through_local_host(hostname: Optional[str]) -> bool:
    """`True`if the event was submitted through a local host, e,g, 127.0.0.1."""
    # testserver is hostname in unit tests
    LOCAL_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1", "testserver"]
    return hostname in LOCAL_HOSTS


analytics_client = AnalyticsClient(
    client_id=CONFIG.cli.analytics_id,
    developer_mode=CONFIG.dev_mode,
    extra_data=None,
    os=system(),
    product_name="fidesops",
    production_version=fides_version,
)


async def send_analytics_event(event: AnalyticsEvent) -> None:
    if CONFIG.user.analytics_opt_out:
        return
    try:
        await analytics_client.send_async(event)
    except AnalyticsError as err:
        log.warning("Error sending analytics event: {}", err)
    else:
        log.info("Analytics event sent with client id: {}", analytics_client.client_id)


async def send_registration(registration: UserRegistration) -> None:
    if CONFIG.user.analytics_opt_out:
        return
    try:
        await analytics_client.register_async(registration.as_fideslog())
    except AnalyticsError as err:
        log.warning("Error sending registration event: {}", err)
    else:
        log.info(
            f"Analytics registration sent with client id: {analytics_client.client_id}"
        )
