"""
Pure response processing utility for async DSR polling.

This module handles data type inference, attachment classification,
and response parsing with no business logic dependencies.
"""

import io
import re
from typing import Any, List, Optional, Union
from urllib.parse import urlparse

import pandas as pd
import pydash
from loguru import logger
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.async_polling_configuration import (
    PollingResult,
    SupportedDataType,
)
from fides.api.util.collection_util import Row


class PollingResponseProcessor:
    """
    Pure utility for processing async polling responses with smart data type inference.

    1. Infers data type from response characteristics
    2. Classifies whether response should be stored as attachment
    3. Processes response into appropriate result format
    """

    @classmethod
    def process_result_response(
        cls, request_path: str, response: Response, result_path: Optional[str] = None
    ) -> PollingResult:
        """
        Process response with smart data type inference.

        Args:
            response: HTTP response object
            request_path: Path that was requested
            result_path: Optional path to extract data from JSON responses

        Returns:
            PollingResult with processed data
        """
        # Step 1: Infer data type
        inferred_type = _infer_data_type(request_path, response)

        # Step 2: Determine if this should be treated as an attachment
        if _should_store_as_attachment(response, inferred_type):
            # Step 3a: Build attachment result
            return _build_attachment_result(response, request_path, inferred_type)

        # Step 3b: Parse as structured data
        rows = _parse_to_rows(response, inferred_type, result_path)
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

    @staticmethod
    def evaluate_status_response(
        response: Response,
        status_path: str,
        status_completed_value: Optional[Any] = None,
    ) -> bool:
        """Process status response and extract completion status."""
        try:
            response_data = response.json()
        except ValueError as e:
            logger.error(f"Invalid JSON response in status check: {e}")
            return False  # Assuming non-JSON response means not complete

        status_path_value = pydash.get(response_data, status_path)
        return PollingResponseProcessor._evaluate_status_value(
            status_path_value, status_completed_value
        )

    @staticmethod
    def _evaluate_status_value(
        status_path_value: Any, status_completed_value: Optional[Any]
    ) -> bool:
        """Evaluate a status value against the completed value."""
        # Boolean direct check
        if isinstance(status_path_value, bool):
            return status_path_value

        # Direct comparison with completed value
        if status_path_value == status_completed_value:
            return True

        # String comparison
        if isinstance(status_path_value, str):
            return PollingResponseProcessor._evaluate_string_status(
                status_path_value, status_completed_value
            )

        # List check (first element)
        if isinstance(status_path_value, list) and status_path_value:
            return PollingResponseProcessor._evaluate_list_status(
                status_path_value, status_completed_value
            )

        # Numeric comparison
        if isinstance(status_path_value, (int, float)):
            return PollingResponseProcessor._evaluate_numeric_status(
                status_path_value, status_completed_value
            )

        # Default to False for unexpected types
        return False

    @staticmethod
    def _evaluate_string_status(
        status_path_value: str, status_completed_value: Optional[Any]
    ) -> bool:
        """Evaluate string status value."""
        # If no completed value specified, any non-empty string is considered complete
        if status_completed_value is None:
            return bool(status_path_value)
        return status_path_value == str(status_completed_value)

    @staticmethod
    def _evaluate_list_status(
        status_path_value: list, status_completed_value: Optional[Any]
    ) -> bool:
        """Evaluate list status value (using first element)."""
        first_element = status_path_value[0]
        if status_completed_value is None:
            return bool(first_element)
        return first_element == status_completed_value

    @staticmethod
    def _evaluate_numeric_status(
        status_path_value: Union[int, float], status_completed_value: Optional[Any]
    ) -> bool:
        """Evaluate numeric status value."""
        if isinstance(status_completed_value, (int, float)):
            return status_path_value == status_completed_value
        return bool(status_path_value)


# Private helpers


def _infer_data_type(request_path: str, response: Response) -> SupportedDataType:
    """Infer data type from response characteristics."""
    # 1. Check Content-Type header
    content_type_result = _infer_from_content_type(response)
    if content_type_result:
        return content_type_result

    # 2. Check URL file extension
    extension_result = _infer_from_file_extension(request_path)
    if extension_result:
        return extension_result

    # 3. Try parsing response body (small sample)
    body_result = _infer_from_response_body(response)
    if body_result:
        return body_result

    # 4. Default fallback
    return SupportedDataType.json


def _infer_from_content_type(response: Response) -> Optional[SupportedDataType]:
    """Infer data type from Content-Type header."""
    content_type = response.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        return SupportedDataType.json
    if "text/csv" in content_type or "application/csv" in content_type:
        return SupportedDataType.csv
    if "application/xml" in content_type or "text/xml" in content_type:
        return SupportedDataType.xml
    if any(
        t in content_type
        for t in ["application/octet-stream", "application/zip", "application/pdf"]
    ):
        return SupportedDataType.attachment

    return None


def _infer_from_file_extension(request_path: str) -> Optional[SupportedDataType]:
    """Infer data type from file extension in URL."""
    parsed_url = urlparse(request_path.lower())
    path = parsed_url.path

    if path.endswith(".csv"):
        return SupportedDataType.csv
    if path.endswith(".json"):
        return SupportedDataType.json
    if path.endswith((".xml", ".xls", ".xlsx")):
        return SupportedDataType.xml
    if path.endswith((".zip", ".pdf", ".tar", ".gz")):
        return SupportedDataType.attachment

    return None


def _infer_from_response_body(response: Response) -> Optional[SupportedDataType]:
    """Infer data type from response body content."""
    try:
        # Try JSON first
        response.json()
        return SupportedDataType.json
    except Exception:  # pylint: disable=bare-except
        # Check if it looks like CSV (look for comma-separated values with headers)
        text_sample = response.text[:500] if hasattr(response, "text") else ""
        if text_sample and "," in text_sample and "\n" in text_sample:
            lines = text_sample.split("\n")[:2]
            if len(lines) >= 2 and len(lines[0].split(",")) == len(lines[1].split(",")):
                return SupportedDataType.csv

    return None


def _should_store_as_attachment(
    response: Response, inferred_type: SupportedDataType
) -> bool:
    """Determine if response should be treated as an attachment."""
    # Check various indicators that suggest this should be an attachment
    return (
        _is_explicit_attachment_type(inferred_type)
        or _has_attachment_content_disposition(response)
        or _has_binary_content_type(response)
        or _is_binary_content(response)
        or _is_large_response(response)
        or _has_file_extension_in_url(response)
    )


def _is_explicit_attachment_type(inferred_type: SupportedDataType) -> bool:
    """Check if the inferred type is explicitly an attachment."""
    return inferred_type == SupportedDataType.attachment


def _has_attachment_content_disposition(response: Response) -> bool:
    """Check if Content-Disposition header indicates attachment."""
    content_disposition = response.headers.get("content-disposition", "").lower()
    return "attachment" in content_disposition


def _has_binary_content_type(response: Response) -> bool:
    """Check if content type indicates binary/file content."""
    content_type = response.headers.get("content-type", "").lower()
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
    return any(bt in content_type for bt in binary_types)


def _is_binary_content(response: Response) -> bool:
    """Check if response content is binary."""
    try:
        # If we can't decode as UTF-8, it's likely binary
        if hasattr(response.content, "__len__") and len(response.content) > 0:
            response.content.decode("utf-8")
        return False
    except (UnicodeDecodeError, AttributeError):
        # Content is binary or can't be decoded - treat as attachment
        return True


def _is_large_response(response: Response) -> bool:
    """Check if response is large enough to be considered a file download."""
    content_length = response.headers.get("content-length")
    if content_length and int(content_length) > 10 * 1024 * 1024:  # > 10MB
        return True
    return False


def _has_file_extension_in_url(response: Response) -> bool:
    """Check if response URL has file-like extensions."""
    request_url = getattr(response, "url", "") or getattr(response.request, "url", "")
    if not isinstance(request_url, str):
        return False

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
    return any(request_url.lower().endswith(ext) for ext in file_extensions)


def _extract_filename(response: Response, request_url: str) -> str:
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


def _build_attachment_result(
    response: Response, request_url: str, inferred_type: SupportedDataType
) -> PollingResult:
    """Build a PollingResult for attachment data."""
    return PollingResult(
        data=response.content,  # Keep as bytes
        result_type="attachment",
        metadata={
            "inferred_type": inferred_type.value,
            "content_type": response.headers.get(
                "content-type", "application/octet-stream"
            ),
            "filename": _extract_filename(response, request_url),
            "size": len(response.content),
            "preserved_as_attachment": True,
        },
    )


def _parse_to_rows(
    response: Response, data_type: SupportedDataType, result_path: Optional[str] = None
) -> List[Row]:
    """
    Parse response to List[Row] based on data type.

    Note: This method is only called for responses that are NOT treated as attachments.
    """
    if data_type == SupportedDataType.json:
        return _parse_json_to_rows(response, result_path)

    if data_type == SupportedDataType.csv:
        return _parse_csv_to_rows(response)

    if data_type == SupportedDataType.xml:
        # Basic XML handling - could be enhanced
        raise PrivacyRequestError("XML parsing not yet implemented")

    if data_type == SupportedDataType.attachment:
        raise PrivacyRequestError(f"Cannot parse {data_type} to rows")

    raise PrivacyRequestError(f"Unsupported data type: {data_type}")


def _parse_json_to_rows(
    response: Response, result_path: Optional[str] = None
) -> List[Row]:
    """Parse JSON response to List[Row]."""
    try:
        json_data = response.json()
    except ValueError as e:
        raise PrivacyRequestError(f"Invalid JSON response: {e}")

    # Extract data using result_path if specified
    if result_path:
        extracted_data = pydash.get(json_data, result_path)
        if extracted_data is None:
            raise PrivacyRequestError(
                f"Could not extract data from response using path: {result_path}"
            )
        json_data = extracted_data

    # Ensure we return a list of dictionaries
    if isinstance(json_data, list):
        return json_data
    if isinstance(json_data, dict):
        return [json_data]
    raise PrivacyRequestError(
        f"Expected list or dict from result request, got: {type(json_data)}"
    )


def _parse_csv_to_rows(response: Response) -> List[Row]:
    """Parse CSV response to List[Row]."""
    try:
        # Use pandas to parse CSV content
        csv_content = response.text
        df = pd.read_csv(io.StringIO(csv_content))

        # Convert to list of dictionaries
        return df.to_dict(orient="records")
    except Exception as e:
        raise PrivacyRequestError(f"Failed to parse CSV response: {e}")
