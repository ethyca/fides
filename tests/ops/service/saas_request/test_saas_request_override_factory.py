from typing import Any, Callable, Dict, List
from uuid import uuid4

import pytest

from fidesops.common_exceptions import (
    InvalidSaaSRequestOverrideException,
    NoSuchSaaSRequestOverrideException,
)
from fidesops.graph.traversal import TraversalNode
from fidesops.models.policy import Policy
from fidesops.models.privacy_request import PrivacyRequest
from fidesops.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
    register,
)
from fidesops.util.collection_util import Row


def uuid():
    return str(uuid4())


def valid_read_override(
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
    param_values_per_row: List[Dict[str, Any]],
    policy: Policy,
    privacy_request: PrivacyRequest,
    secrets: Dict[str, Any],
) -> int:
    """
    A sample override function for update requests with a valid function signature
    """
    pass


@pytest.mark.unit_saas
class TestSaasRequestOverrideFactory:
    """
    Unit tests on SaaS request override factory functionality
    """

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
                override_function, "must declare at least 5 parameters"
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
                override_function, "must declare at least 4 parameters"
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
