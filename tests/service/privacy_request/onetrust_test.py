from unittest import mock
from unittest.mock import Mock, call

import pytest
from fideslib.exceptions import AuthenticationError
from fideslib.models.client import ClientDetail
from sqlalchemy.orm import Session

from fidesops.common_exceptions import (
    PolicyNotFoundException,
    StorageConfigNotFoundException,
)
from fidesops.models.policy import ActionType, Policy, Rule, RuleTarget
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.models.storage import StorageConfig
from fidesops.schemas.storage.storage import StorageDetails, StorageSecrets
from fidesops.schemas.third_party.onetrust import (
    OneTrustRequest,
    OneTrustSubtask,
    OneTrustSubtaskStatus,
)
from fidesops.service.privacy_request.onetrust_service import (
    FIDES_TASK,
    ONETRUST_POLICY_KEY,
    OneTrustService,
)
from fidesops.util.data_category import DataCategory


@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService.transition_status"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.get_onetrust_access_token"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_requests"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_subtasks"
)
@mock.patch(
    "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
)
def test_intake_onetrust_requests_success(
    finish_processing_mock: Mock,
    mock_get_all_subtasks: Mock,
    mock_get_all_requests: Mock,
    mock_get_onetrust_access_token: Mock,
    mock_transition_status: Mock,
    oauth_client: ClientDetail,
    db: Session,
    storage_config_onetrust,
) -> None:
    hostname = storage_config_onetrust.secrets[StorageSecrets.ONETRUST_HOSTNAME.value]
    client = oauth_client
    policy = _create_mock_policy(client, db, storage_config_onetrust)
    # mock onetrust auth
    mock_get_onetrust_access_token.return_value = "124-asdf-23412424"
    TEST_EMAIL = "some-customer@mail.com"

    # mock onetrust requests
    mock_request_1: OneTrustRequest = OneTrustRequest()
    mock_request_1.email = TEST_EMAIL
    mock_request_1.requestQueueRefId = "23xrnqq3crwf"
    mock_request_1.dateCreated = "2021-08-09T12:49:47.983Z"
    mock_request_2: OneTrustRequest = OneTrustRequest()
    mock_request_2.email = "some-other-customer@mail.com"
    mock_request_2.requestQueueRefId = "qo3rucitnwqiu"
    mock_request_1.dateCreated = "2021-09-02T12:03:32.237Z"
    mock_get_all_requests.return_value = [mock_request_1, mock_request_2]

    # mock onetrust subtasks
    mock_subtask_1: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_1.subTaskName = FIDES_TASK
    mock_subtask_1.subTaskId = "1234"
    mock_subtask_2: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_2.subTaskName = "not for fides"
    mock_subtask_2.subTaskId = "4444"
    mock_get_all_subtasks.side_effect = [[mock_subtask_1], [mock_subtask_2]]

    # call test function
    OneTrustService.intake_onetrust_requests(storage_config_onetrust.key)

    # assert
    mock_get_all_requests.assert_called_with(
        hostname,
        mock_get_onetrust_access_token.return_value,
        polling_day_of_week=storage_config_onetrust.details[
            StorageDetails.ONETRUST_POLLING_DAY_OF_WEEK.value
        ],
    )
    mock_get_all_subtasks.assert_has_calls(
        [
            call(
                mock_get_onetrust_access_token.return_value,
                hostname,
                mock_request_1.requestQueueRefId,
            ),
            call(
                mock_get_onetrust_access_token.return_value,
                hostname,
                mock_request_2.requestQueueRefId,
            ),
        ],
        any_order=True,
    )
    mock_transition_status.assert_called_with(
        status=OneTrustSubtaskStatus.COMPLETED,
        hostname=hostname,
        access_token=mock_get_onetrust_access_token.return_value,
        subtask_id=mock_subtask_1.subTaskId,
    )
    pr = PrivacyRequest.get_by(
        db=db,
        field="external_id",
        value=mock_subtask_1.subTaskId,
    )
    persisted_identity = pr.get_persisted_identity()
    assert persisted_identity.email == TEST_EMAIL
    assert pr is not None
    assert finish_processing_mock.called
    # clean up
    policy.delete(db=db)
    client.delete(db=db)
    pr.delete(db=db)


@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.get_onetrust_access_token"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_requests"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_subtasks"
)
@mock.patch(
    "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
)
def test_intake_onetrust_requests_no_config(
    finish_processing_mock: Mock,
    mock_get_all_subtasks: Mock,
    mock_get_all_requests: Mock,
    mock_get_onetrust_access_token: Mock,
    db: Session,
    storage_config_onetrust,
) -> None:
    # mocks case where onetrust storage config gets deleted before task runs
    storage_config_onetrust.delete(db)
    # mock onetrust auth
    mock_get_onetrust_access_token.return_value = "124-asdf-23412424"

    # mock onetrust requests
    mock_request_1: OneTrustRequest = OneTrustRequest()
    mock_request_1.email = "some-customer@mail.com"
    mock_request_1.requestQueueRefId = "23xrnqq3crwf"
    mock_request_1.dateCreated = "2021-08-09T12:49:47.983Z"
    mock_request_2: OneTrustRequest = OneTrustRequest()
    mock_request_2.email = "some-other-customer@mail.com"
    mock_request_2.requestQueueRefId = "qo3rucitnwqiu"
    mock_request_1.dateCreated = "2021-09-02T12:03:32.237Z"
    mock_get_all_requests.return_value = [mock_request_1, mock_request_2]

    # mock onetrust subtasks
    mock_subtask_1: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_1.subTaskName = FIDES_TASK
    mock_subtask_1.subTaskId = "1234"
    mock_subtask_2: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_2.subTaskName = "not for fides"
    mock_subtask_2.subTaskId = "4444"
    mock_get_all_subtasks.side_effect = [[mock_subtask_1], [mock_subtask_2]]

    with pytest.raises(StorageConfigNotFoundException):
        OneTrustService.intake_onetrust_requests(storage_config_onetrust.key)

    pr = PrivacyRequest.get_by(
        db=db,
        field="external_id",
        value=mock_subtask_1.subTaskId,
    )
    assert pr is None
    finish_processing_mock.assert_not_called()


@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.get_onetrust_access_token"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_requests"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_subtasks"
)
@mock.patch(
    "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
)
def test_intake_onetrust_requests_no_policy(
    finish_processing_mock: Mock,
    mock_get_all_subtasks: Mock,
    mock_get_all_requests: Mock,
    mock_get_onetrust_access_token: Mock,
    db: Session,
    storage_config_onetrust,
    oauth_client: ClientDetail,
) -> None:
    client = oauth_client
    # mock onetrust auth
    mock_get_onetrust_access_token.return_value = "124-asdf-23412424"

    # mock onetrust requests
    mock_request_1: OneTrustRequest = OneTrustRequest()
    mock_request_1.email = "some-customer@mail.com"
    mock_request_1.requestQueueRefId = "23xrnqq3crwf"
    mock_request_1.dateCreated = "2021-08-09T12:49:47.983Z"
    mock_request_2: OneTrustRequest = OneTrustRequest()
    mock_request_2.email = "some-other-customer@mail.com"
    mock_request_2.requestQueueRefId = "qo3rucitnwqiu"
    mock_request_1.dateCreated = "2021-09-02T12:03:32.237Z"
    mock_get_all_requests.return_value = [mock_request_1, mock_request_2]

    # mock onetrust subtasks
    mock_subtask_1: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_1.subTaskName = FIDES_TASK
    mock_subtask_1.subTaskId = "1234"
    mock_subtask_2: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_2.subTaskName = "not for fides"
    mock_subtask_2.subTaskId = "4444"
    mock_get_all_subtasks.side_effect = [[mock_subtask_1], [mock_subtask_2]]

    with pytest.raises(PolicyNotFoundException):
        OneTrustService.intake_onetrust_requests(storage_config_onetrust.key)

    pr = PrivacyRequest.get_by(
        db=db,
        field="external_id",
        value=mock_subtask_1.subTaskId,
    )
    assert pr is None
    finish_processing_mock.assert_not_called()
    # clean up
    client.delete(db=db)


@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.get_onetrust_access_token"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_requests"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_subtasks"
)
@mock.patch(
    "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
)
def test_intake_onetrust_requests_auth_fail(
    finish_processing_mock: Mock,
    mock_get_all_subtasks: Mock,
    mock_get_all_requests: Mock,
    mock_get_onetrust_access_token: Mock,
    db: Session,
    storage_config_onetrust,
    oauth_client: ClientDetail,
) -> None:
    client = oauth_client
    policy = _create_mock_policy(client, db, storage_config_onetrust)
    # mock onetrust auth
    mock_get_onetrust_access_token.return_value = None

    # mock onetrust requests
    mock_request_1: OneTrustRequest = OneTrustRequest()
    mock_request_1.email = "some-customer@mail.com"
    mock_request_1.requestQueueRefId = "23xrnqq3crwf"
    mock_request_1.dateCreated = "2021-08-09T12:49:47.983Z"
    mock_request_2: OneTrustRequest = OneTrustRequest()
    mock_request_2.email = "some-other-customer@mail.com"
    mock_request_2.requestQueueRefId = "qo3rucitnwqiu"
    mock_request_1.dateCreated = "2021-09-02T12:03:32.237Z"
    mock_get_all_requests.return_value = [mock_request_1, mock_request_2]

    # mock onetrust subtasks
    mock_subtask_1: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_1.subTaskName = FIDES_TASK
    mock_subtask_1.subTaskId = "1234"
    mock_subtask_2: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_2.subTaskName = "not for fides"
    mock_subtask_2.subTaskId = "4444"
    mock_get_all_subtasks.side_effect = [[mock_subtask_1], [mock_subtask_2]]

    with pytest.raises(AuthenticationError):
        OneTrustService.intake_onetrust_requests(storage_config_onetrust.key)

    pr = PrivacyRequest.get_by(
        db=db,
        field="external_id",
        value=mock_subtask_1.subTaskId,
    )
    assert pr is None
    finish_processing_mock.assert_not_called()
    # clean up
    policy.delete(db=db)
    client.delete(db=db)


@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.get_onetrust_access_token"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_requests"
)
@mock.patch(
    "fidesops.service.privacy_request.onetrust_service.OneTrustService._get_all_subtasks"
)
@mock.patch(
    "fidesops.service.privacy_request.request_runner_service.run_privacy_request.delay"
)
def test_intake_onetrust_requests_no_fides_tasks(
    finish_processing_mock: Mock,
    mock_get_all_subtasks: Mock,
    mock_get_all_requests: Mock,
    mock_get_onetrust_access_token: Mock,
    db: Session,
    storage_config_onetrust,
    oauth_client: ClientDetail,
) -> None:
    hostname = storage_config_onetrust.secrets[StorageSecrets.ONETRUST_HOSTNAME.value]
    client = oauth_client
    policy = _create_mock_policy(client, db, storage_config_onetrust)
    # mock onetrust auth
    mock_get_onetrust_access_token.return_value = "124-asdf-23412424"

    # mock onetrust requests
    mock_request_1: OneTrustRequest = OneTrustRequest()
    mock_request_1.email = "some-customer@mail.com"
    mock_request_1.requestQueueRefId = "23xrnqq3crwf"
    mock_request_1.dateCreated = "2021-08-09T12:49:47.983Z"
    mock_request_2: OneTrustRequest = OneTrustRequest()
    mock_request_2.email = "some-other-customer@mail.com"
    mock_request_2.requestQueueRefId = "qo3rucitnwqiu"
    mock_request_1.dateCreated = "2021-09-02T12:03:32.237Z"
    mock_get_all_requests.return_value = [mock_request_1, mock_request_2]

    # mock onetrust subtasks
    mock_subtask_1: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_1.subTaskName = "some task"
    mock_subtask_1.subTaskId = "1234"
    mock_subtask_2: OneTrustSubtask = OneTrustSubtask()
    mock_subtask_2.subTaskName = "not for fides"
    mock_subtask_2.subTaskId = "4444"
    mock_get_all_subtasks.side_effect = [[mock_subtask_1], [mock_subtask_2]]

    # call test function
    OneTrustService.intake_onetrust_requests(storage_config_onetrust.key)

    # assert
    mock_get_all_requests.assert_called_with(
        hostname,
        mock_get_onetrust_access_token.return_value,
        polling_day_of_week=storage_config_onetrust.details[
            StorageDetails.ONETRUST_POLLING_DAY_OF_WEEK.value
        ],
    )
    mock_get_all_subtasks.assert_has_calls(
        [
            call(
                mock_get_onetrust_access_token.return_value,
                hostname,
                mock_request_1.requestQueueRefId,
            ),
            call(
                mock_get_onetrust_access_token.return_value,
                hostname,
                mock_request_2.requestQueueRefId,
            ),
        ],
        any_order=True,
    )
    pr = PrivacyRequest.get_by(
        db=db,
        field="external_id",
        value=mock_subtask_1.subTaskId,
    )
    assert pr is None
    finish_processing_mock.assert_not_called()
    # clean up
    policy.delete(db=db)
    client.delete(db=db)


def _create_mock_policy(
    client: ClientDetail,
    db: Session,
    storage_config: StorageConfig,
) -> Policy:
    _, policy = Policy.get_or_create(
        db=db,
        data={
            "name": "onetrust policy",
            "key": ONETRUST_POLICY_KEY,
            "client_id": client.id,
        },
    )
    _, rule = Rule.get_or_create(
        db=db,
        data={
            "action_type": ActionType.access,
            "client_id": client.id,
            "name": "onetrust rule",
            "policy_id": policy.id,
            "storage_destination_id": storage_config.id,
        },
    )
    data_category = DataCategory("user.provided.identifiable").value
    RuleTarget.get_or_create(
        db=db,
        data={
            "client_id": client.id,
            "data_category": data_category,
            "name": f"Apply {rule.name} to {data_category}",
            "rule_id": rule.id,
        },
    )
    return policy
