import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, Final, List, Optional, Union

import requests
from requests import Response
from sqlalchemy.orm import Session

from fidesops.common_exceptions import (
    AuthenticationException,
    PolicyNotFoundException,
    StorageConfigNotFoundException,
)
from fidesops.db.session import get_db_session
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.models.storage import StorageConfig
from fidesops.schemas.privacy_request import PrivacyRequestIdentity
from fidesops.schemas.shared_schemas import FidesOpsKey
from fidesops.schemas.storage.storage import StorageDetails, StorageSecrets
from fidesops.schemas.third_party.onetrust import (
    OneTrustGetRequestsResponse,
    OneTrustGetSubtasksResponse,
    OneTrustRequest,
    OneTrustSubtask,
    OneTrustSubtaskStatus,
)
from fidesops.service.outbound_urn_registry import (
    ONETRUST_GET_ALL_REQUESTS,
    ONETRUST_GET_SUBTASKS_BY_REF_ID,
    ONETRUST_PUT_SUBTASK_STATUS,
)
from fidesops.service.privacy_request.request_runner_service import PrivacyRequestRunner
from fidesops.util.cache import get_cache
from fidesops.util.storage_authenticator import get_onetrust_access_token

logger = logging.getLogger(__name__)

ONETRUST_POLICY_KEY = "onetrust"
FIDES_TASK = "fides task"


class OneTrustService:
    """OneTrust Service for privacy requests"""

    @staticmethod
    def intake_onetrust_requests(config_key: FidesOpsKey) -> None:
        """Intake onetrust requests"""
        SessionLocal = get_db_session()
        db = SessionLocal()

        onetrust_config: Optional[StorageConfig] = StorageConfig.get_by(
            db=db, field="key", value=config_key
        )

        if onetrust_config is None:
            raise StorageConfigNotFoundException(
                f"Storage config not found with key: {config_key}"
            )
        if onetrust_config.secrets is None:
            raise StorageConfigNotFoundException(
                f"Storage config secrets not found with key: {config_key}"
            )
        onetrust_policy: Final[Policy] = OneTrustService._get_onetrust_policy(db)
        if onetrust_policy is None:
            raise PolicyNotFoundException(
                f"Policy not found with key: {ONETRUST_POLICY_KEY}"
            )
        hostname: Final[str] = onetrust_config.secrets[
            StorageSecrets.ONETRUST_HOSTNAME.value
        ]
        access_token: Final[str] = get_onetrust_access_token(
            client_id=onetrust_config.secrets[StorageSecrets.ONETRUST_CLIENT_ID.value],
            client_secret=onetrust_config.secrets[
                StorageSecrets.ONETRUST_CLIENT_SECRET.value
            ],
            hostname=hostname,
        )
        if not access_token:
            raise AuthenticationException(
                f"Authentication denied for storage config with key: {config_key}"
            )
        all_requests: Final[List[OneTrustRequest]] = OneTrustService._get_all_requests(
            hostname,
            access_token,
            polling_day_of_week=onetrust_config.details[
                StorageDetails.ONETRUST_POLLING_DAY_OF_WEEK.value
            ],
        )
        for request in all_requests:
            identity_kwargs = {"email": request.email}
            identity = PrivacyRequestIdentity(**identity_kwargs)
            fides_task: Optional[OneTrustSubtask] = OneTrustService._get_fides_subtask(
                hostname, request.requestQueueRefId, access_token
            )
            if fides_task is None:
                # no fides task associated with this request
                continue
            OneTrustService._create_privacy_request(
                fides_task.subTaskId,
                request.dateCreated,
                identity,
                onetrust_policy,
                hostname,
                access_token,
                db,
            )
        db.close()

    @staticmethod
    def transition_status(
        status: OneTrustSubtaskStatus, access_token: str, hostname: str, subtask_id: str
    ) -> None:
        """Given a new status, and external id, updates status of associated onetrust subtask"""
        put_subtask_status_data = {"status": status.value}
        headers = {"Authorization": f"Bearer {access_token}"}
        api_response: Response = requests.put(
            ONETRUST_PUT_SUBTASK_STATUS.format(
                hostname=hostname,
                subtask_id=subtask_id,
            ),
            data=put_subtask_status_data,
            headers=headers,
        )
        if api_response.status_code != 200:
            logger.error(
                f"Unable to set status for onetrust subtask with id: {subtask_id}"
            )

    @staticmethod
    def _create_privacy_request(  # pylint: disable=R0913
        subtask_id: str,
        requested_at: str,
        identity: PrivacyRequestIdentity,
        onetrust_policy: Policy,
        hostname: str,
        access_token: str,
        db: Session,
    ) -> None:
        """create privacy request from onetrust intake"""
        # requested_at is in ISO 8601 format, e.g. 2021-08-09T12:49:47.983Z
        requested_at_date: str = requested_at[0 : requested_at.find("T")]
        requested_at_formatted: datetime = datetime.fromisoformat(requested_at_date)
        kwargs = {
            "requested_at": requested_at_formatted,
            "created_at": datetime.now(),
            "policy_id": onetrust_policy.id,
            "status": "pending",
            "client_id": onetrust_policy.client_id,
            "external_id": subtask_id,
        }
        privacy_request: PrivacyRequest = PrivacyRequest.create(db=db, data=kwargs)
        privacy_request.cache_identity(identity)
        try:
            PrivacyRequestRunner(
                cache=get_cache(),
                privacy_request=privacy_request,
            ).submit()
            request_status = OneTrustSubtaskStatus.COMPLETED
        except BaseException:  # pylint: disable=W0703
            request_status = OneTrustSubtaskStatus.FAILED
        OneTrustService.transition_status(
            status=request_status,
            hostname=hostname,
            access_token=access_token,
            subtask_id=subtask_id,
        )

    @staticmethod
    def _get_onetrust_policy(db: Session) -> Policy:
        """get onetrust policy by key"""
        return Policy.get_by(
            db=db,
            field="key",
            value=ONETRUST_POLICY_KEY,
        )

    @staticmethod
    def _get_fides_subtask(
        hostname: str, request_queue_ref_id: str, access_token: str
    ) -> Optional[OneTrustSubtask]:
        """get Fides subtask associated with request"""
        all_subtasks: List[OneTrustSubtask] = OneTrustService._get_all_subtasks(
            access_token, hostname, request_queue_ref_id
        )
        for subtask in all_subtasks:
            if subtask.subTaskName == FIDES_TASK:
                return subtask
        return None

    @staticmethod
    def _get_all_subtasks(
        access_token: str, hostname: str, request_queue_ref_id: str
    ) -> List[OneTrustSubtask]:
        get_subtasks_params = {"page": 0, "size": 500}
        headers = {"Authorization": f"Bearer {access_token}"}
        all_subtasks: List[OneTrustSubtask] = []
        more_results: bool = False
        while more_results:
            api_response: OneTrustGetSubtasksResponse = requests.get(
                ONETRUST_GET_SUBTASKS_BY_REF_ID.format(
                    hostname=hostname, request_queue_ref_id=request_queue_ref_id
                ),
                params=get_subtasks_params,
                headers=headers,
            ).json()
            all_subtasks.extend(api_response.content)
            more_results = not api_response.last
            get_subtasks_params["page"] += 1
        return all_subtasks

    @staticmethod
    def _get_all_requests(
        hostname: str, access_token: str, polling_day_of_week: int
    ) -> List[OneTrustRequest]:
        """Get all onetrust requests"""
        get_requests_params: Dict[str, Union[int, str]] = {
            "status": urllib.parse.quote("In Progress"),
            "createddate": (
                datetime.today() - timedelta(days=polling_day_of_week)
            ).strftime("%Y%m%d"),
            "page": 0,
            "size": 500,
            "sort": "createdDate,asc",
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        all_requests: List[OneTrustRequest] = []
        more_results = False
        while more_results:
            api_response: OneTrustGetRequestsResponse = requests.get(
                ONETRUST_GET_ALL_REQUESTS.format(hostname=hostname),
                params=get_requests_params,
                headers=headers,
            ).json()
            all_requests.extend(api_response.content)
            more_results = not api_response.last
            get_requests_params["page"] += 1  # type: ignore
        return all_requests
