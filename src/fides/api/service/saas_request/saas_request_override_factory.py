from enum import Enum
from inspect import Signature, signature
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Union

from loguru import logger

from fides.api.common_exceptions import (
    InvalidSaaSRequestOverrideException,
    NoSuchSaaSRequestOverrideException,
)
from fides.api.schemas.consentable_item import ConsentableItem, ConsentWebhookResult
from fides.api.schemas.saas.shared_schemas import ConsentPropagationStatus
from fides.api.util.collection_util import Row

if TYPE_CHECKING:
    from fides.api.schemas.saas.async_polling_configuration import PollingResult


# at some point this should likely be formalized more centrally...
class SaaSRequestType(Enum):
    """
    An `Enum` containing the different possible types of SaaS requests
    """

    TEST = "test"
    READ = "read"
    UPDATE = "update"
    DATA_PROTECTION_REQUEST = "data_protection_request"
    DELETE = "delete"
    OPT_IN = "opt_in"
    OPT_OUT = "opt_out"
    GET_CONSENTABLE_ITEMS = "get_consentable_items"
    UPDATE_CONSENT = "update_consent"
    PROCESS_CONSENT_WEBHOOK = "process_consent_webhook"

    # Async polling request types
    POLLING_STATUS = "polling_status"
    POLLING_RESULT = "polling_result"


RequestOverrideFunction = Callable[
    ...,
    Union[
        ConsentWebhookResult,
        List[ConsentableItem],
        List[Row],
        ConsentPropagationStatus,
        int,
        bool,  # For polling status overrides
        "PollingResult",  # For polling result overrides - string literal to avoid circular import
        None,
    ],
]


class SaaSRequestOverrideFactory:
    """
    Factory class responsible for registering, maintaining, and providing
    user-defined functions that act as overrides to SaaS request execution
    """

    registry: Dict[SaaSRequestType, Dict[str, RequestOverrideFunction]] = {}
    valid_overrides: Dict[SaaSRequestType, str] = {}

    # initialize each request type's inner dicts with an empty dict
    for request_type in SaaSRequestType:
        registry[request_type] = {}
        valid_overrides[request_type] = ""

    @classmethod
    def register(cls, name: str, request_types: List[SaaSRequestType]) -> Callable[
        [RequestOverrideFunction],
        RequestOverrideFunction,
    ]:
        """
        Decorator to register the custom-implemented SaaS request override
        with the given name.
        """

        if isinstance(request_types, SaaSRequestType):
            request_types = [request_types]
        elif not request_types:
            raise TypeError(
                "At least one SaaSRequestType must be specified when registering SaaS request override function {name}"
            )

        def wrapper(
            override_function: RequestOverrideFunction,
        ) -> RequestOverrideFunction:
            for request_type in request_types:
                logger.debug(
                    "Registering new SaaS request override function '{}' under name '{}' for SaaSRequestType {}",
                    override_function.__name__,
                    name,
                    request_type,
                )

                # perform some basic validation on the function that's been provided
                if request_type is SaaSRequestType.TEST:
                    validate_test_override_function(override_function)
                elif request_type is SaaSRequestType.READ:
                    validate_read_override_function(override_function)
                elif request_type in (
                    SaaSRequestType.UPDATE,
                    SaaSRequestType.DELETE,
                    SaaSRequestType.DATA_PROTECTION_REQUEST,
                ):
                    validate_update_override_function(override_function)
                elif request_type in (SaaSRequestType.OPT_IN, SaaSRequestType.OPT_OUT):
                    validate_consent_override_function(override_function)
                elif request_type == SaaSRequestType.GET_CONSENTABLE_ITEMS:
                    validate_get_consentable_item_function(override_function)
                elif request_type == SaaSRequestType.UPDATE_CONSENT:
                    validate_update_consent_function(override_function)
                elif request_type == SaaSRequestType.PROCESS_CONSENT_WEBHOOK:
                    validate_process_consent_webhook_function(override_function)
                elif request_type == SaaSRequestType.POLLING_STATUS:
                    validate_polling_status_override_function(override_function)
                elif request_type == SaaSRequestType.POLLING_RESULT:
                    validate_polling_result_override_function(override_function)
                else:
                    raise ValueError(
                        f"Invalid SaaSRequestType '{request_type}' provided for SaaS request override function"
                    )

                if name in cls.registry[request_type]:
                    logger.warning(
                        "SaaS request override function with name '{}' already exists for SaaSRequestType {}. It previously referred to function '{}', but will now refer to '{}'",
                        name,
                        request_type,
                        cls.registry[request_type][name],
                        override_function.__name__,
                    )

                cls.registry[request_type][name] = override_function
                cls.valid_overrides[request_type] = ", ".join(
                    cls.registry[request_type].keys()
                )

            return override_function

        return wrapper

    @classmethod
    def get_override(
        cls, override_function_name: str, request_type: SaaSRequestType
    ) -> RequestOverrideFunction:
        """
        Returns the request override function given the name.
        Raises NoSuchSaaSRequestOverrideException if the named override
        does not exist.
        """
        try:
            override_function: RequestOverrideFunction = cls.registry[request_type][
                override_function_name
            ]
        except KeyError:
            raise NoSuchSaaSRequestOverrideException(
                f"Custom SaaS override '{override_function_name}' does not exist. Valid custom SaaS override classes for SaaSRequestType {request_type} are [{cls.valid_overrides[request_type]}]"
            )
        return override_function


def validate_test_override_function(f: Callable) -> None:
    """
    Perform some basic checks on the user-provided SaaS request override function
    that will be used with `test` actions.

    The validation is not overly strict to allow for some flexibility in
    the functions that are used for overrides, but we check to ensure that
    the function meets the framework's basic expectations.

    Specifically, the validation checks that function declares at least 2 parameters.
    """
    sig: Signature = signature(f)
    if len(sig.parameters) < 2:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must declare at least 2 parameters"
        )


def validate_read_override_function(f: Callable) -> None:
    """
    Perform some basic checks on the user-provided SaaS request override function
    that will be used with `read` actions.

    The validation is not overly strict to allow for some flexibility in
    the functions that are used for overrides, but we check to ensure that
    the function meets the framework's basic expectations.

    Specifically, the validation checks that function's return type is `List[Row]`
    and that it declares at least 6 parameters.
    """
    sig: Signature = signature(f)
    if sig.return_annotation != List[Row]:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must return a List[Row]"
        )
    if len(sig.parameters) < 6:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must declare at least 6 parameters"
        )


def validate_update_override_function(f: Callable) -> None:
    """
    Perform some basic checks on the user-provided SaaS request override function
    that will be used with `update`, `delete` or `data_protection_request` actions.

    The validation is not overly strict to allow for some flexibility in
    the functions that are used for overrides, but we check to ensure that
    the function meets the framework's basic expectations.

    Specifically, the validation checks that function's return type is `int`
    and that it declares at least 4 parameters.
    """
    sig: Signature = signature(f)
    if sig.return_annotation is not int:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must return an int"
        )
    if len(sig.parameters) < 5:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must declare at least 5 parameters"
        )


def validate_consent_override_function(f: Callable) -> None:
    """
    Perform some basic checks on the user-provided SaaS request override function
    that will be used with `consent` actions.

    The validation is not overly strict to allow for some flexibility in
    the functions that are used for overrides, but we check to ensure that
    the function meets the framework's basic expectations.

    Specifically, the validation checks that function's return type is `ConsentPropagationStatus`
    and that it declares at least 4 parameters.
    """
    sig: Signature = signature(f)
    if sig.return_annotation is not ConsentPropagationStatus:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must return a ConsentPropagationStatus"
        )
    if len(sig.parameters) < 4:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must declare at least 4 parameters"
        )


def validate_get_consentable_item_function(f: Callable) -> None:
    pass


def validate_update_consent_function(f: Callable) -> None:
    """Used for notice-based SaaS consent flow"""
    sig: Signature = signature(f)
    if sig.return_annotation is not ConsentPropagationStatus:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS update consent function must return a ConsentPropagationStatus"
        )
    if len(sig.parameters) < 5:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS update consent function must declare at least 5 parameters"
        )


def validate_process_consent_webhook_function(f: Callable) -> None:
    sig: Signature = signature(f)
    if sig.return_annotation is not ConsentWebhookResult:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS process consent webhook function must return a ConsentWebhookResult"
        )
    if len(sig.parameters) < 4:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS process consent webhook function must declare at least 4 parameters"
        )


def validate_polling_status_override_function(f: Callable) -> None:
    """
    Perform some basic checks on the user-provided SaaS request override function
    that will be used for polling status checks.

    The validation is not overly strict to allow for some flexibility in
    the functions that are used for overrides, but we check to ensure that
    the function meets the framework's basic expectations.

    Specifically, the validation checks that function's return type is `bool`
    and that it declares at least 4 parameters.
    """
    sig: Signature = signature(f)
    if sig.return_annotation is not bool:
        raise InvalidSaaSRequestOverrideException(
            "Polling status override function must return a bool"
        )
    if len(sig.parameters) < 4:
        raise InvalidSaaSRequestOverrideException(
            "Polling status override function must declare at least 4 parameters"
        )


def validate_polling_result_override_function(f: Callable) -> None:
    """
    Perform some basic checks on the user-provided SaaS request override function
    that will be used for polling result retrieval.

    The validation is not overly strict to allow for some flexibility in
    the functions that are used for overrides, but we check to ensure that
    the function meets the framework's basic expectations.

    Specifically, the validation checks that function's return type is `PollingResult`
    and that it declares at least 4 parameters.
    """
    sig: Signature = signature(f)

    # Import PollingResult here to avoid circular imports at module level
    from fides.api.schemas.saas.async_polling_configuration import PollingResult

    # Check return type annotation - handle both direct class and string literals
    return_annotation = sig.return_annotation
    if return_annotation not in (
        PollingResult,
        "PollingResult",
        Optional[PollingResult],
        "Optional[PollingResult]",
    ):
        raise InvalidSaaSRequestOverrideException(
            "Polling result override function must return a PollingResult"
        )
    if len(sig.parameters) < 4:
        raise InvalidSaaSRequestOverrideException(
            "Polling result override function must declare at least 4 parameters"
        )


# TODO: Avoid running this on import?
register = SaaSRequestOverrideFactory.register
