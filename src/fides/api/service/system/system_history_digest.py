from datetime import datetime, timedelta

import requests
from loguru import logger
from sqlalchemy import distinct
from sqlalchemy.orm import joinedload

from fides.api.models.sql_models import System
from fides.api.models.system_history import SystemHistory
from fides.api.tasks import DatabaseTask, celery_app
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.config import get_config

CONFIG = get_config()
SYSTEM_CHANGE_DIGEST = "batch_email_send"


@celery_app.task(base=DatabaseTask, bind=True)
def send_system_change_digest(self: DatabaseTask) -> None:
    logger.info("Starting system change digest send...")
    with self.get_new_session() as session:
        # create a subquery to get distinct system_keys from SystemHistory in the last 24 hours
        subquery = (
            session.query(distinct(SystemHistory.system_key).label("system_key"))
            .filter(SystemHistory.created_at > datetime.now() - timedelta(hours=24))
            .subquery()
        )

        # join the subquery with the System table to get unique systems
        modified_systems = (
            session.query(System)
            .join(subquery, System.fides_key == subquery.c.system_key)
            .all()
        )

        if modified_systems:
            webhook_url = CONFIG.jobs.system_change_webhook_url
            response = requests.post(
                webhook_url,  # type: ignore
                data={
                    "modified_systems": [
                        {"fides_key": system.fides_key, "name": system.name}
                        for system in modified_systems
                    ]
                },
            )
            if response.ok:
                logger.info(
                    f"Successfully posted system change digest to {webhook_url}"
                )
            else:
                logger.error(f"Unable to post system change digest to {webhook_url}")


def initiate_scheduled_system_change_digest() -> None:
    """Initiates scheduler post system change digests to a specified webhook"""

    if CONFIG.test_mode:
        return

    # don't schedule the job if the webhook url isn't defined
    if not CONFIG.jobs.system_change_webhook_url:
        return

    assert (
        scheduler.running
    ), "Scheduler is not running! Cannot add system change digest job."

    logger.info("Initiating scheduler for system change digest")
    scheduler.add_job(
        func=send_system_change_digest,
        kwargs={},
        id=SYSTEM_CHANGE_DIGEST,
        coalesce=False,
        replace_existing=True,
        trigger="cron",
        minute="0",
        hour="6",
        timezone="US/Eastern",
    )
