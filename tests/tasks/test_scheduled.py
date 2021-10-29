from typing import Any
from unittest import mock
from unittest.mock import Mock

from apscheduler.triggers.cron import CronTrigger

from fidesops.schemas.storage.storage import (
    StorageDetails,
)
from fidesops.tasks.scheduled.tasks import (
    get_scheduler,
    initiate_scheduled_request_intake,
    ONETRUST_INTAKE_TASK,
)


def test_initiate_scheduled_request_intake(storage_config_onetrust) -> None:
    initiate_scheduled_request_intake()
    scheduler = get_scheduler()
    assert scheduler.running
    job = scheduler.get_job(job_id=ONETRUST_INTAKE_TASK)
    assert job is not None
    assert isinstance(job.trigger, CronTrigger)
    assert job.trigger.fields[4].name == "day_of_week"
    assert (
        job.trigger.fields[4].expressions[0].first
        == storage_config_onetrust.details[
            StorageDetails.ONETRUST_POLLING_DAY_OF_WEEK.value
        ]
    )

    assert job.trigger.fields[5].name == "hour"
    assert (
        job.trigger.fields[5].expressions[0].first
        == storage_config_onetrust.details[StorageDetails.ONETRUST_POLLING_HR.value]
    )
