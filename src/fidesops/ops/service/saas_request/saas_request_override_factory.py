import logging
from enum import Enum
from inspect import Signature, signature
from typing import Callable, Dict, List, Union

from fidesops.ops.common_exceptions import (
    InvalidSaaSRequestOverrideException,
    NoSuchSaaSRequestOverrideException,
)
from fidesops.ops.util.collection_util import Row

logger = logging.getLogger(__name__)

# at some point this should likely be formalized more centrally...
class SaaSRequestType(Enum):
    """
    An `Enum` containing the different possible types of SaaS requests
    """

    READ = "read"
    UPDATE = "update"
    DATA_PROTECTION_REQUEST = "data_protection_request"
    DELETE = "delete"


class SaaSRequestOverrideFactory:
    """
    Factory class responsible for registering, maintaining, and providing
    user-defined functions that act as overrides to SaaS request execution
    """

    registry: Dict[
        SaaSRequestType, Dict[str, Callable[..., Union[List[Row], int]]]
    ] = {}
    valid_overrides: Dict[SaaSRequestType, str] = {}

    # initialize each request type's inner dicts with an empty dict
    for request_type in SaaSRequestType:
        registry[request_type] = {}
        valid_overrides[request_type] = ""

    @classmethod
    def register(
        cls, name: str, request_types: List[SaaSRequestType]
    ) -> Callable[
        [Callable[..., Union[List[Row], int]]], Callable[..., Union[List[Row], int]]
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
            override_function: Callable[..., Union[List[Row], int]],
        ) -> Callable[..., Union[List[Row], int]]:
            for request_type in request_types:
                logger.debug(
                    "Registering new SaaS request override function '%s' under name '%s' for SaaSRequestType %s",
                    override_function.__name__,
                    name,
                    request_type,
                )

                # perform some basic validation on the function that's been provided
                if request_type is SaaSRequestType.READ:
                    validate_read_override_function(override_function)
                elif request_type in (
                    SaaSRequestType.UPDATE,
                    SaaSRequestType.DELETE,
                    SaaSRequestType.DATA_PROTECTION_REQUEST,
                ):
                    validate_update_override_function(override_function)
                else:
                    raise ValueError(
                        f"Invalid SaaSRequestType '{request_type}' provided for SaaS request override function"
                    )

                if name in cls.registry[request_type]:
                    logger.warning(
                        "SaaS request override function with name '%s' already exists for SaaSRequestType %s. It previously referred to function '%s', but will now refer to '%s'",
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
    ) -> Callable[..., Union[List[Row], int]]:
        """
        Returns the request override function given the name.
        Raises NoSuchSaaSRequestOverrideException if the named override
        does not exist.
        """
        try:
            override_function: Callable[..., Union[List[Row], int]] = cls.registry[
                request_type
            ][override_function_name]
        except KeyError:
            raise NoSuchSaaSRequestOverrideException(
                f"Custom SaaS override '{override_function_name}' does not exist. Valid custom SaaS override classes for SaaSRequestType {request_type} are [{cls.valid_overrides[request_type]}]"
            )
        return override_function


def validate_read_override_function(f: Callable) -> None:
    """
    Perform some basic checks on the user-provided SaaS request override function
    that will be used with `read` actions.

    The validation is not overly strict to allow for some flexibility in
    the functions that are used for overrides, but we check to ensure that
    the function meets the framework's basic expectations.

    Specifically, the validation checks that function's return type is `List[Row]`
    and that it declares at least 5 parameters.
    """
    sig: Signature = signature(f)
    if sig.return_annotation is not List[Row]:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must return a List[Row]"
        )
    if len(sig.parameters) < 5:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must declare at least 5 parameters"
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
    if len(sig.parameters) < 4:
        raise InvalidSaaSRequestOverrideException(
            "Provided SaaS request override function must declare at least 4 parameters"
        )


register = SaaSRequestOverrideFactory.register
