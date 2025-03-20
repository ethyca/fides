import random
from typing import Any, Dict

import pytest

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.connectors.saas_connector import ConsentPropagationStatus
from fides.api.service.privacy_request.request_runner_service import (
    build_consent_dataset_graph,
)
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
    register,
)
from tests.conftest import consent_runner_tester
from tests.ops.integration_tests.saas.connector_runner import (
    create_privacy_preference_history,
)


@register("opt_in_request_override", [SaaSRequestType.OPT_IN])
def opt_in_request_override(
    client: AuthenticatedClient,
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> ConsentPropagationStatus:
    """A sample opt-in request override"""
    return ConsentPropagationStatus.executed


@register("opt_out_request_override", [SaaSRequestType.OPT_OUT])
def opt_out_request_override(
    client: AuthenticatedClient,
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> ConsentPropagationStatus:
    """A sample opt-out request override"""
    return ConsentPropagationStatus.executed


class TestConsentRequestOverride:
    @pytest.mark.parametrize(
        "dsr_version, opt_in, expected_override_function_name, expected_saas_request_type",
        [
            ("use_dsr_3_0", False, "opt_out_request_override", SaaSRequestType.OPT_OUT),
            ("use_dsr_2_0", False, "opt_out_request_override", SaaSRequestType.OPT_OUT),
            ("use_dsr_3_0", True, "opt_in_request_override", SaaSRequestType.OPT_IN),
            ("use_dsr_2_0", True, "opt_in_request_override", SaaSRequestType.OPT_IN),
        ],
    )
    def test_old_consent_request(
        self,
        db,
        consent_policy: Policy,
        saas_consent_request_override_connection_config,
        saas_consent_request_override_dataset_config,
        privacy_request,
        dsr_version,
        request,
        mocker,
        opt_in,
        expected_override_function_name,
        expected_saas_request_type,
    ):
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        saas_config = saas_consent_request_override_connection_config.get_saas_config()
        dataset_name = saas_config.fides_key

        privacy_request.consent_preferences = [
            {"data_use": "marketing.advertising", "opt_in": opt_in}
        ]
        privacy_request.save(db)

        spy = mocker.spy(SaaSRequestOverrideFactory, "get_override")

        v = consent_runner_tester(
            privacy_request,
            consent_policy,
            build_consent_dataset_graph([saas_consent_request_override_dataset_config]),
            [saas_consent_request_override_connection_config],
            {"email": "user@example.com"},
            db,
        )
        assert v == {f"{dataset_name}:{dataset_name}": True}
        spy.assert_called_once_with(
            expected_override_function_name, expected_saas_request_type
        )

    @pytest.mark.parametrize(
        "dsr_version, opt_in, expected_override_function_name, expected_saas_request_type",
        [
            ("use_dsr_3_0", False, "opt_out_request_override", SaaSRequestType.OPT_OUT),
            ("use_dsr_2_0", False, "opt_out_request_override", SaaSRequestType.OPT_OUT),
            ("use_dsr_3_0", True, "opt_in_request_override", SaaSRequestType.OPT_IN),
            ("use_dsr_2_0", True, "opt_in_request_override", SaaSRequestType.OPT_IN),
        ],
    )
    async def test_new_consent_request(
        self,
        db,
        consent_policy,
        saas_consent_request_override_connection_config,
        saas_consent_request_override_dataset_config,
        privacy_request,
        dsr_version,
        request,
        mocker,
        opt_in,
        expected_override_function_name,
        expected_saas_request_type,
    ) -> None:
        request.getfixturevalue(dsr_version)  # REQUIRED to test both DSR 3.0 and 2.0

        saas_config = saas_consent_request_override_connection_config.get_saas_config()
        dataset_name = saas_config.fides_key

        identities = {"email": "user@example.com"}
        privacy_request = PrivacyRequest(
            id=f"test_consent_request_task_{random.randint(0, 1000)}",
            status=PrivacyRequestStatus.pending,
            policy_id=consent_policy.id,
        )
        privacy_request.save(db)

        spy = mocker.spy(SaaSRequestOverrideFactory, "get_override")

        create_privacy_preference_history(
            db, privacy_request, identities, opt_in=opt_in
        )
        privacy_request.save(db)
        v = consent_runner_tester(
            privacy_request,
            consent_policy,
            build_consent_dataset_graph([saas_consent_request_override_dataset_config]),
            [saas_consent_request_override_connection_config],
            identities,
            db,
        )
        assert v == {f"{dataset_name}:{dataset_name}": True}
        spy.assert_called_once_with(
            expected_override_function_name, expected_saas_request_type
        )
