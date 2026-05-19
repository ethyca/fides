import datetime

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.email_batch_service import (
    BATCH_EMAIL_SEND,
    initiate_scheduled_batch_email_send,
)
from fides.api.service.privacy_request.request_runner_service import (
    initiate_paused_privacy_request_followup,
)
from fides.api.service.privacy_request.request_service import (
    DSR_DATA_REMOVAL,
    PRIVACY_REQUEST_STATUS_CHANGE_POLL,
    initiate_poll_for_exited_privacy_request_tasks,
    initiate_scheduled_dsr_data_removal,
)
from fides.api.tasks.scheduled.scheduler import scheduler
from fides.config import get_config

CONFIG = get_config()


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


def test_initiate_batch_email_send() -> None:
    CONFIG.test_mode = False

    initiate_scheduled_batch_email_send()
    assert scheduler.running
    job = scheduler.get_job(job_id=BATCH_EMAIL_SEND)
    assert job is not None
    assert isinstance(job.trigger, CronTrigger)

    assert job.trigger.fields[4].name == "day_of_week"
    assert str(job.trigger.fields[4].expressions[0]) == "mon"

    assert job.trigger.fields[5].name == "hour"
    assert str(job.trigger.fields[5].expressions[0]) == "12"

    assert type(job.trigger.timezone).__name__ == "US/Eastern"

    CONFIG.test_mode = True


def test_initiate_scheduled_dsr_data_removal() -> None:
    """Currently runs weekly to pick up any Request Tasks that expired in the last week
    or Privacy Requests that need PII removed from them."""
    CONFIG.test_mode = False

    initiate_scheduled_dsr_data_removal()
    assert scheduler.running
    job = scheduler.get_job(job_id=DSR_DATA_REMOVAL)
    assert job is not None
    assert isinstance(job.trigger, CronTrigger)

    assert job.trigger.fields[2].name == "day"
    assert str(job.trigger.fields[2].expressions[0]) == "*"

    assert job.trigger.fields[5].name == "hour"
    assert str(job.trigger.fields[5].expressions[0]) == "2"

    assert type(job.trigger.timezone).__name__ == "US/Eastern"

    CONFIG.test_mode = True


def test_initiate_poll_for_exited_privacy_request_tasks() -> None:
    """This task runs on an interval looking for Privacy Requests that need to change state
    because all their Request Tasks have had a chance to run but some are errored"""
    CONFIG.test_mode = False

    initiate_poll_for_exited_privacy_request_tasks()
    assert scheduler.running
    job = scheduler.get_job(job_id=PRIVACY_REQUEST_STATUS_CHANGE_POLL)
    assert job is not None
    assert isinstance(job.trigger, IntervalTrigger)
    assert job.trigger.interval == datetime.timedelta(
        seconds=CONFIG.execution.state_polling_interval
    )

    CONFIG.test_mode = True
