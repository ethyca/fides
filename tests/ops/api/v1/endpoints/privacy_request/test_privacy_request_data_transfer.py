from starlette.testclient import TestClient

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.common.api.scope_registry import PRIVACY_REQUEST_TRANSFER
from fides.common.api.v1.urn_registry import (
    PRIVACY_REQUEST_TRANSFER_TO_PARENT,
    V1_URL_PREFIX,
)


class TestPrivacyRequestDataTransfer:
    """Additional tests for the privacy_request_data_transfer endpoint to cover error paths."""

    def test_privacy_request_data_transfer_no_access_results(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        policy,
        db,
    ) -> None:
        """If no access results exist for the privacy request, we should receive a 404."""
        pr = privacy_request.save(db=db)

        # Authorize with correct scope
        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_TRANSFER])
        rule_key = policy.get_rules_for_action(ActionType.access)[0].key

        response = api_client.get(
            f"{V1_URL_PREFIX}{PRIVACY_REQUEST_TRANSFER_TO_PARENT.format(privacy_request_id=pr.id, rule_key=rule_key)}",
            headers=auth_header,
        )

        assert response.status_code == 404
        assert "No access request information found" in response.json()["detail"]

    def test_privacy_request_data_transfer_no_datasets(
        self,
        api_client: TestClient,
        generate_auth_header,
        privacy_request,
        policy,
        db,
        monkeypatch,
    ) -> None:
        """If datasets cannot be found, the endpoint should return a 404."""
        pr = privacy_request.save(db=db)

        # Provide mock access results so we bypass the first 404 path
        monkeypatch.setattr(
            PrivacyRequest,
            "get_raw_access_results",
            lambda self: {"dummy_dataset": []},
            raising=True,
        )

        auth_header = generate_auth_header(scopes=[PRIVACY_REQUEST_TRANSFER])
        rule_key = policy.get_rules_for_action(ActionType.access)[0].key

        response = api_client.get(
            f"{V1_URL_PREFIX}{PRIVACY_REQUEST_TRANSFER_TO_PARENT.format(privacy_request_id=pr.id, rule_key=rule_key)}",
            headers=auth_header,
        )

        assert response.status_code == 404
        assert "No datasets found" in response.json()["detail"]
