from typing import Any, Callable, Dict, List
from uuid import uuid4

import pytest

from fides.api.common_exceptions import (
    InvalidSaaSRequestOverrideException,
    NoSuchSaaSRequestOverrideException,
)
from fides.api.graph.traversal import TraversalNode
from fides.api.models.consent_automation import ConsentableItem
from fides.api.models.policy import Policy
from fides.api.models.privacy_notice import UserConsentPreference
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.consentable_item import ConsentWebhookResult
from fides.api.schemas.saas.shared_schemas import ConsentPropagationStatus
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row


def uuid():
    return str(uuid4())


def valid_test_override(
    client: AuthenticatedClient,
    secrets: Dict[str, Any],
) -> None:
    """
    A sample override function for test requests with a valid function signature
    """
    pass


def valid_read_override(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    A sample override function for read requests with a valid function signature
    """
    pass


def valid_read_override_copy(
    client: AuthenticatedClient,
    node: TraversalNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    A copy sample override function for read requests with a valid function signature
    """
    pass


def valid_update_override(
    client: AuthenticatedClient,
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    A sample override function for update requests with a valid function signature
    """
    pass


def valid_consent_override(
    client: AuthenticatedClient,
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> ConsentPropagationStatus:
    """
    A sample override function for consent requests with a valid function signature
    """
    return ConsentPropagationStatus.executed


def valid_consent_update_override(
    client: AuthenticatedClient,
    secrets: Dict[str, Any],
    input_data: Dict[str, List[Any]],
    notice_id_to_preference_map: Dict[str, UserConsentPreference],
    consentable_items_hierarchy: List[ConsentableItem],
) -> ConsentPropagationStatus:
    """
    A sample override function for consent update requests with a valid function signature
    """
    return ConsentPropagationStatus.executed


def valid_process_consent_webhook_override(
    client: AuthenticatedClient,
    secrets: Dict[str, Any],
    payload: Any,
    notice_id_to_preference_map: Dict[str, UserConsentPreference],
    consentable_items: List[ConsentableItem],
) -> ConsentWebhookResult:
    """
    A sample override function for process consent webhook requests with a valid function signature
    """
    return ConsentWebhookResult()


@pytest.mark.unit_saas
class TestSaasRequestOverrideFactory:
    """
    Unit tests on SaaS request override factory functionality
    """

    def test_register_test(self):
        """
        Test registering a valid `test` override function
        """
        f_id = uuid()
        register(f_id, SaaSRequestType.TEST)(valid_test_override)
        assert valid_test_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.TEST
        )

        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.READ)
        assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

    def test_register_read(self):
        """
        Test registering a valid `read` override function
        """
        f_id = uuid()
        register(f_id, SaaSRequestType.READ)(valid_read_override)
        assert valid_read_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )

        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.UPDATE)
        assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

    def test_register_update(self):
        """
        Test registering a valid `update` override function
        """
        f_id = uuid()
        register(f_id, SaaSRequestType.UPDATE)(valid_update_override)
        assert valid_update_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.UPDATE
        )

        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.READ)
        assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

    def test_register_update_and_delete(self):
        """
        Test registering a valid override function for both `update` and `delete`
        """
        f_id = uuid()
        register(f_id, [SaaSRequestType.UPDATE, SaaSRequestType.DELETE])(
            valid_update_override
        )
        assert valid_update_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.UPDATE
        )
        assert valid_update_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.DELETE
        )

        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.READ)
        assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

    def test_register_opt_in_consent(self):
        """
        Test registering a valid `opt_in` override function
        """

        f_id = uuid()
        register(f_id, SaaSRequestType.OPT_IN)(valid_consent_override)
        assert valid_consent_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.OPT_IN
        )

        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.READ)
        assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

    def test_register_opt_out_consent(self):
        """
        Test registering a valid `opt_out` override function
        """

        f_id = uuid()
        register(f_id, SaaSRequestType.OPT_OUT)(valid_consent_override)
        assert valid_consent_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.OPT_OUT
        )

        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.READ)
        assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

    def test_register_update_consent_override(self):
        """
        Test registering a valid `update_consent` override function
        """

        f_id = uuid()
        register(f_id, SaaSRequestType.UPDATE_CONSENT)(valid_consent_update_override)
        assert valid_consent_update_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.UPDATE_CONSENT
        )

        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.READ)
        assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

    def test_register_process_consent_webhook_override(self):
        """
        Test registering a valid `process_consent_webhook` override function
        """

        f_id = uuid()
        register(f_id, SaaSRequestType.PROCESS_CONSENT_WEBHOOK)(
            valid_process_consent_webhook_override
        )
        assert (
            valid_process_consent_webhook_override
            == SaaSRequestOverrideFactory.get_override(
                f_id, SaaSRequestType.PROCESS_CONSENT_WEBHOOK
            )
        )

        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.READ)
        assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

    def test_reregister_override(self):
        """
        Test that registering a new override with the same ID and same request type
        properly updates what is returned by the factory.
        """
        f_id = uuid()
        register(f_id, SaaSRequestType.READ)(valid_read_override)
        assert valid_read_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )

        register(f_id, SaaSRequestType.READ)(valid_read_override_copy)
        assert valid_read_override_copy == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )
        assert valid_read_override != SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )

    def test_register_different_id_override(self):
        """
        Test that registering a new override with a different ID and same request
        type properly creates two separate entries that can each be retrieved
        """
        f_id = uuid()
        register(f_id, SaaSRequestType.READ)(valid_read_override)
        assert valid_read_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )

        f_id_2 = uuid()
        register(f_id_2, SaaSRequestType.READ)(valid_read_override_copy)
        assert valid_read_override_copy == SaaSRequestOverrideFactory.get_override(
            f_id_2, SaaSRequestType.READ
        )
        assert valid_read_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )

    def test_register_same_id_different_request_type(self):
        """
        Test that registering a new override with the same ID but a different
        request type does NOT update the first entry
        """
        f_id = uuid()
        register(f_id, SaaSRequestType.READ)(valid_read_override)
        assert valid_read_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )

        register(f_id, SaaSRequestType.UPDATE)(valid_update_override)
        assert valid_update_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.UPDATE
        )
        assert valid_read_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )

    def test_register_invalid_test(self):
        """
        Test registering some invalid `test` override functions is handled
        as expected
        """
        f_id = uuid()

        def too_few_params(client: AuthenticatedClient) -> List[Row]:
            pass

        def no_params() -> List[Row]:
            pass

        params_functions = [too_few_params, no_params]

        def assert_validation_error(override_function: Callable, exc_string: str):
            with pytest.raises(InvalidSaaSRequestOverrideException) as exc:
                register(f_id, SaaSRequestType.TEST)(override_function)
            assert exc_string in str(exc.value)
            with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
                SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.TEST)
            assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

        for override_function in params_functions:
            assert_validation_error(
                override_function, "must declare at least 2 parameters"
            )

    def test_register_invalid_read(self):
        """
        Test registering some invalid `read` override functions is handled
        as expected
        """
        f_id = uuid()

        def no_return_type(
            node: TraversalNode,
            policy: Policy,
            privacy_request: PrivacyRequest,
            input_data: Dict[str, List[Any]],
            secrets: Dict[str, Any],
        ):
            pass

        def invalid_return_type(
            node: TraversalNode,
            policy: Policy,
            privacy_request: PrivacyRequest,
            input_data: Dict[str, List[Any]],
            secrets: Dict[str, Any],
        ) -> int:
            pass

        def invalid_return_type_2(
            node: TraversalNode,
            policy: Policy,
            privacy_request: PrivacyRequest,
            input_data: Dict[str, List[Any]],
            secrets: Dict[str, Any],
        ) -> List[str]:
            pass

        def too_few_params(
            node: TraversalNode,
            policy: Policy,
            privacy_request: PrivacyRequest,
            input_data: Dict[str, List[Any]],
        ) -> List[Row]:
            pass

        def no_params() -> List[Row]:
            pass

        return_type_functions = [
            invalid_return_type,
            invalid_return_type_2,
            no_return_type,
        ]
        params_functions = [too_few_params, no_params]

        def assert_validation_error(override_function: Callable, exc_string: str):
            with pytest.raises(InvalidSaaSRequestOverrideException) as exc:
                register(f_id, SaaSRequestType.READ)(override_function)
            assert exc_string in str(exc.value)
            with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
                SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.READ)
            assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

        for override_function in return_type_functions:
            assert_validation_error(override_function, "must return a List[Row]")

        for override_function in params_functions:
            assert_validation_error(
                override_function, "must declare at least 6 parameters"
            )

    def test_register_invalid_update(self):
        """
        Test that registering some invalid `update` override functions is
        handled as expected
        """
        f_id = uuid()

        def no_return_type(
            param_values_per_row: List[Dict[str, Any]],
            policy: Policy,
            privacy_request: PrivacyRequest,
            secrets: Dict[str, Any],
        ):
            pass

        def invalid_return_type(
            param_values_per_row: List[Dict[str, Any]],
            policy: Policy,
            privacy_request: PrivacyRequest,
            secrets: Dict[str, Any],
        ) -> str:
            pass

        def invalid_return_type_2(
            param_values_per_row: List[Dict[str, Any]],
            policy: Policy,
            privacy_request: PrivacyRequest,
            secrets: Dict[str, Any],
        ) -> List[Row]:
            pass

        def too_few_params(
            param_values_per_row: List[Dict[str, Any]],
            policy: Policy,
            privacy_request: PrivacyRequest,
        ) -> int:
            pass

        def no_params() -> int:
            pass

        def assert_validation_error(override_function: Callable, exc_string: str):
            with pytest.raises(InvalidSaaSRequestOverrideException) as exc:
                register(f_id, SaaSRequestType.UPDATE)(override_function)
            assert exc_string in str(exc.value)
            with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
                SaaSRequestOverrideFactory.get_override(f_id, SaaSRequestType.UPDATE)
            assert f"Custom SaaS override '{f_id}' does not exist." in str(exc.value)

        return_type_functions = [
            invalid_return_type,
            invalid_return_type_2,
            no_return_type,
        ]
        params_functions = [too_few_params, no_params]

        for override_function in return_type_functions:
            assert_validation_error(override_function, "must return an int")

        for override_function in params_functions:
            assert_validation_error(
                override_function, "must declare at least 5 parameters"
            )

    def test_register_invalid_request_type(self):
        """
        Test that registering an override functions with an invalid (or no)
        request type specified is handled as expected (with an error)
        """
        f_id = uuid()
        with pytest.raises(TypeError) as exc:
            register(f_id)(valid_read_override)
        assert "missing 1 required positional argument" in str(exc.value)

        with pytest.raises(TypeError) as exc:
            register(f_id, [])(valid_read_override)
        assert "At least one SaaSRequestType must be specified" in str(exc.value)

        with pytest.raises(TypeError) as exc:
            register(f_id, {})(valid_read_override)
        assert "At least one SaaSRequestType must be specified" in str(exc.value)

        with pytest.raises(ValueError) as exc:
            register(f_id, "an invalid string")(valid_read_override)
        assert "Invalid SaaSRequestType" in str(exc.value)

        with pytest.raises(TypeError) as exc:
            register(f_id, 1)(valid_read_override)

        with pytest.raises(ValueError) as exc:
            register(f_id, [SaaSRequestType.READ, "an invalid string"])(
                valid_read_override
            )
        assert "Invalid SaaSRequestType" in str(exc.value)

    def test_retrieve_incorrect_id(self):
        """
        Test that trying to retrieve an override function by passing
        an incorrect ID is handled as expected
        """
        f_id = uuid()
        register(f_id, SaaSRequestType.READ)(valid_read_override)
        assert valid_read_override == SaaSRequestOverrideFactory.get_override(
            f_id, SaaSRequestType.READ
        )

        f_id_2 = uuid()
        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(f_id_2, SaaSRequestType.READ)
        assert f"Custom SaaS override '{f_id_2}' does not exist." in str(exc.value)
