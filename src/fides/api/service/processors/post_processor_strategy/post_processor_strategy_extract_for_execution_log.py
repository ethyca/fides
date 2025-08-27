from typing import Any, Dict, List, Optional, Union

import pydash
from loguru import logger
from requests import Response

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.saas.strategy_configuration import (
    ExtractForExecutionLogPostProcessorConfiguration,
)
from fides.api.service.execution_context import add_execution_log_message
from fides.api.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)


class ExtractForExecutionLogPostProcessorStrategy(PostProcessorStrategy):
    """Postprocessor that extracts data from API response contents and adds it to execution log messages"""

    name = "extract_for_execution_log"
    configuration_model = ExtractForExecutionLogPostProcessorConfiguration

    def __init__(self, configuration: ExtractForExecutionLogPostProcessorConfiguration):
        self.configuration = configuration

    def process(
        self,
        data: Union[List[Dict[str, Any]], Dict[str, Any]],
        identity_data: Optional[Dict[str, Any]] = None,
        privacy_request: Optional[PrivacyRequest] = None,
        response: Optional[Response] = None,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extract data from response contents and add to execution log messages.
        Data is passed through unchanged (non-destructive postprocessor).
        """
        config = self.configuration

        try:
            # Only process if response.contents is available
            if response is None or not response.content:
                return data

            if config.path is None:
                # No path specified - use entire response contents as string
                message = str(response.content)
            else:
                # Attempt to parse the response content as JSON before extracting
                try:
                    json_data: Any = response.json()
                except ValueError:
                    logger.debug(
                        "Unable to parse response content as JSON for path extraction"
                    )
                    return data

                extracted_value = pydash.get(json_data, config.path)
                if extracted_value is None:
                    logger.debug(f"No data found at path '{config.path}'")
                    return data

                message = str(extracted_value)

            # Add message to execution context
            add_execution_log_message(message)
            logger.info(message)

        except Exception as e:
            error_msg = f"Error in extract_for_execution_log postprocessor: {e}"
            logger.error(error_msg)
            add_execution_log_message(error_msg)

        return data
