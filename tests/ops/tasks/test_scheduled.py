from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from fides.api.ops.models.privacy_request import PrivacyRequestStatus
from fides.api.ops.schemas.storage.storage import StorageDetails
from fides.api.ops.service.privacy_request.request_runner_service import (
    initiate_paused_privacy_request_followup,
)
from fides.api.ops.tasks.scheduled.scheduler import scheduler


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
