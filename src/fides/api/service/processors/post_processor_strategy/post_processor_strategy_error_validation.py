from typing import Any, Dict, List, Union

from requests import Response

from fides.api.schemas.saas.strategy_configuration import (
    ErrorValidationPostProcessorConfiguration,
)
from fides.api.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)


class ErrorValidationPostProcessorStrategy(PostProcessorStrategy):
    """
    Expands on the ignore_errors flag.Validates that a Given error is a non-critical error that can be ignored
    There are some API's where diferent errors have the same error code (I.E 400).
    For those cases, we need to check the message in order to figure out if the error is ignorable

    E.g:
    ignorable_response = [
        "HttpCode" : 400
        "status" : "error",
        "message" : "example@email.com is already unsubscribed from subscription 1234567",
    ]
    v/s
    non_ignorable_response = [
        "HttpCode" : 400
        "status" : "error",
        "message" : "Given account does not have permissions to remove the content ",
    ]
    """

    name = "error_validation"
    ##TODO: Check configuration model
    configuration_model = ErrorValidationPostProcessorConfiguration

    def __init__(self, configuration: ErrorValidationPostProcessorConfiguration):
        self.http_code = configuration.http_code
        self.expected_message = configuration.expected_message
        self.error_message_field = configuration.error_message_field

    def process(
        self,
        data: Any,
        response: Response = None,
        identity_data: Dict[str, Any] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        :param data: A list or dict
        :param Response: The Response given by the endpoint
        :param identity_data: dict of cached identity data
        :return: data for processing
        """
        if response is None:
            return data

        response_json = response.json()
        error_message = response_json.get(self.error_message_field)
        ## TODO: expand for multiple error messages
        if (
            response.status_code == self.http_code
            and self.expected_message in error_message
        ):
            ## Managed similar to saas_connector::handle_error_response: return empty
            return []
        ## Else, we proceed as normal
        return data
