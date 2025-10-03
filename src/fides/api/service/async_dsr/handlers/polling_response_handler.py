"""
Pure response processing utility for async DSR polling.

This module handles data type inference, attachment classification,
and response parsing with no business logic dependencies.
"""

import mimetypes
import os
from email.message import Message
from typing import Any, List, Optional
from urllib.parse import urlparse

import pydash
from loguru import logger
from requests import Response

from fides.api.common_exceptions import PrivacyRequestError
from fides.api.schemas.saas.async_polling_configuration import (
    PollingResult,
    PollingResultType,
    SupportedDataType,
)
from fides.api.util.collection_util import Row

CONTENT_TYPE = "content-type"
CONTENT_DISPOSITION = "content-disposition"

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
    ".csv",
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
    "text/csv",
    "application/csv",
}

# Initialize mimetypes module for content type inference
mimetypes.init()


class PollingResponseProcessor:
    """Pure utility for processing async polling responses with smart data type inference."""

    @classmethod
    def process_result_response(
        cls, request_path: str, response: Response, result_path: Optional[str] = None
    ) -> PollingResult:
        """Process response with smart data type inference."""
        inferred_type = cls._infer_data_type(request_path, response)

        if cls._should_store_as_attachment(response, request_path, inferred_type):
            return cls._build_attachment_result(response, request_path, inferred_type)

        rows = cls._parse_to_rows(response, inferred_type, result_path)
        return PollingResult(
            data=rows,
            result_type=PollingResultType.rows,
            metadata={
                "inferred_type": inferred_type.value,
                "content_type": response.headers.get(CONTENT_TYPE, ""),
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
        content_type = response.headers.get(CONTENT_TYPE, "").lower()
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

    @staticmethod
    def _infer_data_type(request_path: str, response: Response) -> SupportedDataType:
        """Infer data type from response characteristics."""
        content_type = response.headers.get(CONTENT_TYPE, "").lower()

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

    @staticmethod
    def _should_store_as_attachment(
        response: Response, request_path: str, inferred_type: SupportedDataType
    ) -> bool:
        """Determine if response should be treated as an attachment."""
        content_type = response.headers.get(CONTENT_TYPE, "").lower()

        # Check attachment-specific indicators
        if inferred_type == SupportedDataType.attachment:
            return True

        if "attachment" in response.headers.get(CONTENT_DISPOSITION, "").lower():
            return True

        if any(ct in content_type for ct in ATTACHMENT_CONTENT_TYPES):
            return True

        # Check file extension in URL
        path = urlparse(request_path.lower()).path
        if any(path.endswith(ext) for ext in ATTACHMENT_EXTENSIONS):
            return True

        return False

    @staticmethod
    def _extract_filename(response: Response, request_url: str) -> str:
        """Extract filename from response or URL."""
        # Try Content-Disposition header using email.message for proper parsing
        disposition = response.headers.get(CONTENT_DISPOSITION)
        if disposition:
            msg = Message()
            msg[CONTENT_DISPOSITION] = disposition
            filename = msg.get_filename()
            if filename:
                return filename

        # Extract from URL path using os.path.basename
        path = urlparse(request_url).path
        if path:
            filename = os.path.basename(path)
            if filename:
                return filename

        return "polling_result"

    @staticmethod
    def _build_attachment_result(
        response: Response, request_url: str, inferred_type: SupportedDataType
    ) -> PollingResult:
        """Build a PollingResult for attachment data."""
        filename = PollingResponseProcessor._extract_filename(response, request_url)

        # Get content type from header, or infer from filename extension
        content_type = response.headers.get(CONTENT_TYPE)

        # If no content type or it's generic, try to infer from filename extension using mimetypes
        if not content_type or content_type in (
            "application/octet-stream",
            "text/plain",
        ):
            guessed_type, _ = mimetypes.guess_type(filename)
            if guessed_type:
                content_type = guessed_type
            else:
                content_type = content_type or "application/octet-stream"

        return PollingResult(
            data=response.content,
            result_type=PollingResultType.attachment,
            metadata={
                "inferred_type": inferred_type.value,
                "content_type": content_type,
                "filename": filename,
                "size": len(response.content),
                "preserved_as_attachment": True,
            },
        )

    @staticmethod
    def _parse_to_rows(
        response: Response,
        data_type: SupportedDataType,
        result_path: Optional[str] = None,
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

        raise PrivacyRequestError(f"Cannot parse {data_type} to rows")
