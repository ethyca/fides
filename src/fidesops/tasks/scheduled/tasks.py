import logging
from typing import Optional

from apscheduler.jobstores.base import JobLookupError

from fidesops.db.session import get_db_session
from fidesops.models.storage import StorageConfig
from fidesops.schemas.shared_schemas import FidesOpsKey
from fidesops.schemas.storage.storage import StorageDetails, StorageType
from fidesops.service.privacy_request.onetrust_service import OneTrustService
from fidesops.tasks.scheduled.scheduler import scheduler

logger = logging.getLogger(__name__)

ONETRUST_INTAKE_TASK = "onetrust_intake"


def initiate_scheduled_request_intake() -> None:
    """Initiates scheduler to add request intake tasks"""
    SessionLocal = get_db_session()
    db = SessionLocal()
    onetrust_config: Optional[StorageConfig] = StorageConfig.get_by(
        db=db, field="type", value=StorageType.onetrust
    )
    if onetrust_config is not None:
        logger.info("Initiating request intake for OneTrust.")
        scheduler.add_job(
            func=_intake_onetrust_requests,
            kwargs={"config_key": onetrust_config.key},
            id=ONETRUST_INTAKE_TASK,
            # This means any overlapping invocations of the function will stack and run in succession
            coalesce=False,
            # This allows us not to check for any existing OneTrust fetch jobs currently on this scheduler
            replace_existing=True,
            trigger="cron",
            hour=onetrust_config.details[StorageDetails.ONETRUST_POLLING_HR.value],
            minute=0,
            day_of_week=onetrust_config.details[
                StorageDetails.ONETRUST_POLLING_DAY_OF_WEEK.value
            ],
        )
    else:
        try:
            scheduler.remove_job(job_id=ONETRUST_INTAKE_TASK)
        except JobLookupError:
            # This job isn't currently configured on the scheduler, so we don't need to remove it
            pass
    db.close()


def _intake_onetrust_requests(config_key: FidesOpsKey) -> None:
    """Begins onetrust request intake"""
    OneTrustService.intake_onetrust_requests(config_key)
