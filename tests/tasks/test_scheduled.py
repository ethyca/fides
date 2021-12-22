from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from fidesops.models.privacy_request import PrivacyRequestStatus
from fidesops.schemas.storage.storage import (
    StorageDetails,
)
from fidesops.service.privacy_request.request_runner_service import (
    initiate_paused_privacy_request_followup,
)
from fidesops.tasks.scheduled.scheduler import scheduler
from fidesops.tasks.scheduled.tasks import (
    initiate_scheduled_request_intake,
    ONETRUST_INTAKE_TASK,
)


def test_initiate_scheduled_request_intake(storage_config_onetrust) -> None:
    initiate_scheduled_request_intake()
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


def test_initiate_scheduled_paused_privacy_request_followup(
    privacy_request, db
) -> None:
    privacy_request.status = PrivacyRequestStatus.paused
    privacy_request.save(db=db)
    initiate_paused_privacy_request_followup(privacy_request)
    assert scheduler.running
    job = scheduler.get_job(job_id=privacy_request.id)
    assert job is not None
    assert isinstance(job.trigger, DateTrigger)
