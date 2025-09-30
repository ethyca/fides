"""
Pure response processing utility for async DSR polling.

This module handles data type inference, attachment classification,
and response parsing with no business logic dependencies.
"""

import io
import re
from typing import Any, List, Optional
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

# Content type mappings for data type detection
CONTENT_TYPE_MAP = {
    "application/json": SupportedDataType.json,
    "text/csv": SupportedDataType.csv,
    "application/csv": SupportedDataType.csv,
}

# File extensions that indicate attachments
ATTACHMENT_EXTENSIONS = {
    ".zip",
    ".pdf",
    ".tar",
    ".gz",
    ".xlsx",
    ".xls",
    ".xml",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".webp",
    ".svg",
}

# Content types that should always be attachments
ATTACHMENT_CONTENT_TYPES = {
    "application/octet-stream",
    "application/zip",
    "application/pdf",
    "application/xml",
    "text/xml",
    "image/",
    "video/",
}

# Content type inference from file extensions
EXTENSION_CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".json": "application/json",
    ".csv": "text/csv",
    ".xml": "application/xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


class PollingResponseProcessor:
    """Pure utility for processing async polling responses with smart data type inference."""

    @classmethod
    def process_result_response(
        cls, request_path: str, response: Response, result_path: Optional[str] = None
    ) -> PollingResult:
        """Process response with smart data type inference."""
        inferred_type = _infer_data_type(request_path, response)

        if _should_store_as_attachment(response, request_path, inferred_type):
            return _build_attachment_result(response, request_path, inferred_type)

        rows = _parse_to_rows(response, inferred_type, result_path)
        return PollingResult(
            data=rows,
            result_type="rows",
            metadata={
                "inferred_type": inferred_type.value,
                "content_type": response.headers.get("content-type", ""),
                "row_count": len(rows),
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
        # Check if response is JSON
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" not in content_type:
            return False

        try:
            status_value = pydash.get(response.json(), status_path)
        except ValueError as e:
            logger.error(f"Invalid JSON response in status check: {e}")
            return False

        # Handle list values - check first element
        if isinstance(status_value, list) and status_value:
            status_value = status_value[0]

        # Direct comparison if completed value specified
        if status_completed_value is not None:
            return status_value == status_completed_value

        # Otherwise, check truthiness
        return bool(status_value)


# Private helpers


def _infer_data_type(request_path: str, response: Response) -> SupportedDataType:
    """Infer data type from response characteristics."""
    content_type = response.headers.get("content-type", "").lower()

    # Check for attachment content types first
    if any(ct in content_type for ct in ATTACHMENT_CONTENT_TYPES):
        return SupportedDataType.attachment

    # Check content-type header (most reliable)
    for content_type_pattern, data_type in CONTENT_TYPE_MAP.items():
        if content_type_pattern in content_type:
            return data_type

    # Check URL extension
    path = urlparse(request_path.lower()).path
    if path.endswith(".csv"):
        return SupportedDataType.csv

    # Try parsing as JSON
    try:
        response.json()
        return SupportedDataType.json
    except (ValueError, TypeError):
        pass

    return SupportedDataType.attachment  # Preserve unknown types as raw data


def _should_store_as_attachment(
    response: Response, request_path: str, inferred_type: SupportedDataType
) -> bool:
    """Determine if response should be treated as an attachment."""
    content_type = response.headers.get("content-type", "").lower()

    # Check attachment-specific indicators
    if inferred_type == SupportedDataType.attachment:
        return True

    if "attachment" in response.headers.get("content-disposition", "").lower():
        return True

    if any(ct in content_type for ct in ATTACHMENT_CONTENT_TYPES):
        return True

    # Check file extension in URL
    path = urlparse(request_path.lower()).path
    if any(path.endswith(ext) for ext in ATTACHMENT_EXTENSIONS):
        return True

    return False


def _extract_filename(response: Response, request_url: str) -> str:
    """Extract filename from response or URL."""
    # Try Content-Disposition header
    disposition = response.headers.get("content-disposition", "")
    match = re.search(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)', disposition)
    if match:
        filename = match.group(1).strip("'\"")
        if filename:
            return filename

    # Extract from URL path
    path = urlparse(request_url).path
    if path:
        filename = path.split("/")[-1]
        if filename:
            return filename

    return "polling_result"


def _build_attachment_result(
    response: Response, request_url: str, inferred_type: SupportedDataType
) -> PollingResult:
    """Build a PollingResult for attachment data."""
    filename = _extract_filename(response, request_url)

    # Get content type from header, or infer from filename extension
    content_type = response.headers.get("content-type")

    # If no content type or it's generic, try to infer from filename extension
    if not content_type or content_type in ("application/octet-stream", "text/plain"):
        for ext, mime_type in EXTENSION_CONTENT_TYPES.items():
            if filename.lower().endswith(ext):
                content_type = mime_type
                break
        else:
            content_type = (
                content_type or "application/octet-stream"
            )  # Keep original or fallback

    return PollingResult(
        data=response.content,
        result_type="attachment",
        metadata={
            "inferred_type": inferred_type.value,
            "content_type": content_type,
            "filename": filename,
            "size": len(response.content),
            "preserved_as_attachment": True,
        },
    )


def _parse_to_rows(
    response: Response, data_type: SupportedDataType, result_path: Optional[str] = None
) -> List[Row]:
    """Parse response to List[Row] based on data type."""
    if data_type == SupportedDataType.json:
        try:
            data = response.json()
            if result_path:
                data = pydash.get(data, result_path)
                if data is None:
                    raise PrivacyRequestError(
                        f"Could not extract data from response using path: {result_path}"
                    )

            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
            raise PrivacyRequestError(
                f"Expected list or dict from result request, got: {type(data)}"
            )

        except ValueError as e:
            raise PrivacyRequestError(f"Invalid JSON response: {e}")

    if data_type == SupportedDataType.csv:
        try:
            df = pd.read_csv(io.StringIO(response.text))
            return df.to_dict(orient="records")
        except Exception as e:
            raise PrivacyRequestError(f"Failed to parse CSV: {e}")

    raise PrivacyRequestError(f"Cannot parse {data_type} to rows")
