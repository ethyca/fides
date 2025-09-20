import io
import re
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

import pandas as pd
import pydash
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.models.privacy_request.request_task import AsyncTaskType
from fides.api.schemas.saas.async_polling_configuration import (
    PollingAsyncDSRConfiguration,
    PollingResult,
    SupportedDataType,
)
from fides.api.service.async_dsr.async_dsr_strategy import AsyncDSRStrategy
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
)
from fides.api.util.collection_util import Row
from fides.api.util.saas_util import map_param_values


class PollingAsyncDSRStrategy(AsyncDSRStrategy):
    """
    Unified strategy for polling async DSR requests.
    Works for both access and erasure operations.
    """

    type = AsyncTaskType.polling
    configuration_model = PollingAsyncDSRConfiguration

    def __init__(self, configuration: PollingAsyncDSRConfiguration):
        self.status_request = configuration.status_request
        self.result_request = configuration.result_request

    def get_status_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> bool:
        """Execute status request with override support and return completion status."""

        # Check for request override first
        if self.status_request.request_override:
            # Get and execute override function
            override_function = SaaSRequestOverrideFactory.get_override(
                self.status_request.request_override, SaaSRequestType.POLLING_STATUS
            )

            return override_function(
                client=client,
                param_values=param_values,
                request_config=self.status_request,
                secrets=secrets,
            )

        # Standard status checking logic
        return self._execute_standard_status_request(client, param_values)

    def _execute_standard_status_request(
        self, client: AuthenticatedClient, param_values: Dict[str, Any]
    ) -> bool:
        """Execute standard status request logic."""
        prepared_status_request = map_param_values(
            "status", "polling request", self.status_request, param_values
        )

        response: Response = client.send(prepared_status_request)

        if response.ok:
            status_path_value = pydash.get(response.json(), self.status_request.status_path)
            return self._evaluate_status_value(status_path_value)

        raise PrivacyRequestError(
            f"Status request failed with status code {response.status_code}: {response.text}"
        )

    def get_result_request(
        self,
        client: AuthenticatedClient,
        param_values: Dict[str, Any],
        secrets: Dict[str, Any],
    ) -> PollingResult:
        """Execute result request with override support and return smart-parsed results."""

        # Check for request override first
        if self.result_request.request_override:
            # Get and execute override function
            override_function = SaaSRequestOverrideFactory.get_override(
                self.result_request.request_override, SaaSRequestType.POLLING_RESULT
            )

            return override_function(
                client=client,
                param_values=param_values,
                request_config=self.result_request,
                secrets=secrets,
            )

        # Standard result processing logic
        return self._execute_standard_result_request(client, param_values)

    def _execute_standard_result_request(
        self, client: AuthenticatedClient, param_values: Dict[str, Any]
    ) -> PollingResult:
        """Execute standard result request logic."""
        prepared_result_request = map_param_values(
            "result", "polling request", self.result_request, param_values
        )

        response: Response = client.send(prepared_result_request)

        if not response.ok:
            raise PrivacyRequestError(
                f"Result request failed with status code {response.status_code}: {response.text}"
            )

        # Smart inference and processing
        return self._process_response_with_inference(
            response, prepared_result_request.path or ""
        )

    def _evaluate_status_value(self, status_path_value: Any) -> bool:
        """Evaluate if status indicates completion."""
        # Boolean direct check
        if isinstance(status_path_value, bool):
            return status_path_value

        # Direct comparison with completed value
        if status_path_value == self.status_request.status_completed_value:
            return True

        # String comparison
        if isinstance(status_path_value, str):
            # If no completed value specified, any non-empty string is considered complete
            if self.status_request.status_completed_value is None:
                return bool(status_path_value)
            return status_path_value == str(self.status_request.status_completed_value)

        # List check (first element)
        if isinstance(status_path_value, list) and status_path_value:
            first_element = status_path_value[0]
            if self.status_request.status_completed_value is None:
                return bool(first_element)
            return first_element == self.status_request.status_completed_value

        # Numeric comparison
        if isinstance(status_path_value, (int, float)):
            if isinstance(self.status_request.status_completed_value, (int, float)):
                return status_path_value == self.status_request.status_completed_value
            return bool(status_path_value)

        # Default to False for unexpected types
        return False

    def _process_response_with_inference(
        self, response: Response, request_url: str
    ) -> PollingResult:
        """
        Process response with smart data type inference.

        Key principle: If data comes as bytes or is intended as an attachment
        (even JSON/CSV), preserve it as attachment rather than parsing to List[Row].
        """

        # Infer data type from response characteristics
        inferred_type = self._infer_data_type(response, request_url)

        # Determine if this should be treated as an attachment
        # This includes binary data, large files, or responses with file-like characteristics
        if self._is_attachment_response(response, inferred_type):
            # Preserve as attachment - don't parse to rows even if it's JSON/CSV
            return PollingResult(
                data=response.content,  # Keep as bytes
                result_type="attachment",
                metadata={
                    "inferred_type": inferred_type.value,
                    "content_type": response.headers.get(
                        "content-type", "application/octet-stream"
                    ),
                    "filename": self._extract_filename(response, request_url),
                    "size": len(response.content),
                    "preserved_as_attachment": True,
                },
            )
        else:
            # Parse as structured data only for small, clearly structured responses
            rows = self._parse_to_rows(response, inferred_type)
            return PollingResult(
                data=rows,
                result_type="rows",
                metadata={
                    "inferred_type": inferred_type.value,
                    "content_type": response.headers.get("content-type", ""),
                    "row_count": len(rows) if isinstance(rows, list) else 0,
                    "parsed_to_rows": True,
                },
            )

    def _infer_data_type(
        self, response: Response, request_url: str
    ) -> SupportedDataType:
        """Infer data type from response characteristics."""

        # 1. Check Content-Type header
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            return SupportedDataType.json
        elif "text/csv" in content_type or "application/csv" in content_type:
            return SupportedDataType.csv
        elif "application/xml" in content_type or "text/xml" in content_type:
            return SupportedDataType.xml
        elif any(
            t in content_type
            for t in ["application/octet-stream", "application/zip", "application/pdf"]
        ):
            return SupportedDataType.attachment

        # 2. Check URL file extension
        parsed_url = urlparse(request_url.lower())
        path = parsed_url.path
        if path.endswith(".csv"):
            return SupportedDataType.csv
        elif path.endswith(".json"):
            return SupportedDataType.json
        elif path.endswith((".xml", ".xls", ".xlsx")):
            return SupportedDataType.xml
        elif path.endswith((".zip", ".pdf", ".tar", ".gz")):
            return SupportedDataType.attachment

        # 3. Try parsing response body (small sample)
        try:
            # Try JSON first
            response.json()
            return SupportedDataType.json
        except:
            # Check if it looks like CSV (look for comma-separated values with headers)
            text_sample = response.text[:500] if hasattr(response, "text") else ""
            if text_sample and "," in text_sample and "\n" in text_sample:
                lines = text_sample.split("\n")[:2]
                if len(lines) >= 2 and len(lines[0].split(",")) == len(
                    lines[1].split(",")
                ):
                    return SupportedDataType.csv

        # 4. Default fallback
        return SupportedDataType.json

    def _is_attachment_response(
        self, response: Response, inferred_type: SupportedDataType
    ) -> bool:
        """Determine if response should be treated as an attachment."""

        # 1. Explicit attachment type
        if inferred_type == SupportedDataType.attachment:
            return True

        # 2. Content-Disposition header indicates attachment
        content_disposition = response.headers.get("content-disposition", "").lower()
        if "attachment" in content_disposition:
            return True

        # 3. Check for binary/file content types
        content_type = response.headers.get("content-type", "").lower()

        # Common file/binary types that should always be attachments
        binary_types = [
            "application/octet-stream",
            "application/zip",
            "application/pdf",
            "application/x-zip-compressed",
            "application/gzip",
            "application/x-tar",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/",
            "audio/",
            "video/",
        ]

        if any(bt in content_type for bt in binary_types):
            return True

        # 4. Check if response content is already bytes and appears to be binary
        # This catches cases where JSON/CSV is delivered as binary attachment data
        try:
            # If we can't decode as UTF-8, it's likely binary
            if hasattr(response.content, "__len__") and len(response.content) > 0:
                response.content.decode("utf-8")
        except (UnicodeDecodeError, AttributeError):
            # Content is binary or can't be decoded - treat as attachment
            return True

        # 5. Large responses are more likely to be file downloads
        # Even if they're JSON/CSV, large responses often indicate file exports
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # > 10MB
            return True

        # 6. Check response URL for file-like patterns
        # URLs ending in file extensions suggest downloadable files
        request_url = getattr(response, "url", "") or getattr(
            response.request, "url", ""
        )
        if isinstance(request_url, str):
            file_extensions = [
                ".json",
                ".csv",
                ".xml",
                ".xlsx",
                ".zip",
                ".pdf",
                ".tar",
                ".gz",
            ]
            if any(request_url.lower().endswith(ext) for ext in file_extensions):
                return True

        return False

    def _extract_filename(self, response: Response, request_url: str) -> str:
        """Extract filename from response or URL."""

        # Try Content-Disposition header first
        content_disposition = response.headers.get("content-disposition", "")
        if content_disposition:
            filename_match = re.search(
                r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', content_disposition
            )
            if filename_match:
                filename = filename_match.group(1).strip("'\"")
                if filename:
                    return filename

        # Extract from URL path
        parsed_url = urlparse(request_url)
        if parsed_url.path:
            path_parts = parsed_url.path.split("/")
            if path_parts and path_parts[-1]:
                return path_parts[-1]

        # Generic fallback
        return "polling_result"

    def _parse_to_rows(
        self, response: Response, data_type: SupportedDataType
    ) -> List[Row]:
        """
        Parse response to List[Row] based on inferred data type.

        Note: This method is only called for responses that are NOT treated as attachments.
        If a response is bytes, binary, or has attachment-like characteristics,
        it will be preserved as an attachment and this method won't be called.
        """

        if data_type == SupportedDataType.json:
            return self._parse_json_to_rows(response)
        elif data_type == SupportedDataType.csv:
            return self._parse_csv_to_rows(response)
        elif data_type == SupportedDataType.xml:
            # Basic XML handling - could be enhanced
            raise PrivacyRequestError("XML parsing not yet implemented")
        else:
            raise PrivacyRequestError(f"Cannot parse {data_type} to rows")

    def _parse_json_to_rows(self, response: Response) -> List[Row]:
        """Parse JSON response to List[Row]."""
        try:
            json_data = response.json()
        except ValueError as e:
            raise PrivacyRequestError(f"Invalid JSON response: {e}")

        # Extract data using result_path if specified
        if self.result_request.result_path:
            extracted_data = pydash.get(json_data, self.result_request.result_path)
            if extracted_data is None:
                raise PrivacyRequestError(
                    f"Could not extract data from response using path: {self.result_request.result_path}"
                )
            json_data = extracted_data

        # Ensure we return a list of dictionaries
        if isinstance(json_data, list):
            return json_data
        elif isinstance(json_data, dict):
            return [json_data]
        else:
            raise PrivacyRequestError(
                f"Expected list or dict from result request, got: {type(json_data)}"
            )

    def _parse_csv_to_rows(self, response: Response) -> List[Row]:
        """Parse CSV response to List[Row]."""
        try:
            # Use pandas to parse CSV content
            csv_content = response.text
            df = pd.read_csv(io.StringIO(csv_content))

            # Convert to list of dictionaries
            return df.to_dict(orient='records')
        except Exception as e:
            raise PrivacyRequestError(f"Failed to parse CSV response: {e}")
