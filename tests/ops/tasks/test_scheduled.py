from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from fides.api.ops.models.privacy_request import PrivacyRequestStatus
from fides.api.ops.service.privacy_request.consent_email_batch_service import (
    BATCH_CONSENT_EMAIL_SEND,
    initiate_scheduled_batch_consent_email_send,
)
from fides.api.ops.service.privacy_request.request_runner_service import (
    initiate_paused_privacy_request_followup,
)
from fides.api.ops.tasks.scheduled.scheduler import scheduler
from fides.core.config import get_config

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


def test_initiate_batch_consent_email_send() -> None:
    CONFIG.test_mode = False

    initiate_scheduled_batch_consent_email_send()
    assert scheduler.running
    job = scheduler.get_job(job_id=BATCH_CONSENT_EMAIL_SEND)
    assert job is not None
    assert isinstance(job.trigger, CronTrigger)

    assert job.trigger.fields[4].name == "day_of_week"
    assert str(job.trigger.fields[4].expressions[0]) == "mon"

    assert job.trigger.fields[5].name == "hour"
    assert str(job.trigger.fields[5].expressions[0]) == "12"

    assert type(job.trigger.timezone).__name__ == "US/Eastern"

    CONFIG.test_mode = True
