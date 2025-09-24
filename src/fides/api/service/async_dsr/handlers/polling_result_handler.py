"""
Response inference utility for async DSR polling.

This utility handles data type inference, attachment classification,
and response parsing for polling results.
"""
import io
import re
from typing import List
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
from fides.api.service.async_dsr.utils import store_polling_attachment
from fides.api.util.collection_util import Row


class PollingResultHandler:
    """
    Handler for processing polling results based on action type.

    Access requests: Adds rows to access_data or stores attachments
    Erasure requests: Records number of affected records
    """

    @classmethod
    def handle_access_result(
        cls,
        db,
        polling_result,
        request_task,
        privacy_request,
        rows_accumulator: List[Row]
    ) -> None:
        """Handle result for access requests."""
        if polling_result.result_type == "rows":
            # Structured data - add to rows collection
            if isinstance(polling_result.data, list):
                rows_accumulator.extend(polling_result.data)
            else:
                logger.warning(
                    f"Expected list for rows result, got {type(polling_result.data)}"
                )

        elif polling_result.result_type == "attachment":
            # File attachment - store and link to request task

            try:
                attachment_id = store_polling_attachment(
                    db=db,
                    attachment_data=polling_result.data,
                    filename=polling_result.metadata.get("filename", "polling_result"),
                    content_type=polling_result.metadata.get(
                        "content_type", "application/octet-stream"
                    ),
                    request_task=request_task,
                    privacy_request=privacy_request,
                )

                # Add attachment metadata to collection data
                cls._add_attachment_metadata_to_rows(db, attachment_id, rows_accumulator)

            except Exception as e:
                raise PrivacyRequestError(f"Attachment storage failed: {e}")
        else:
            raise PrivacyRequestError(f"Unsupported result type: {polling_result.result_type}")

    @classmethod
    def handle_erasure_result(
        cls,
        polling_result,
        request_task,
        affected_records_accumulator: List[int]
    ) -> None:
        """Handle result for erasure requests."""
        if polling_result.result_type == "rows":
            # For erasure, rows typically contain info about what was deleted
            # The count represents affected records
            if isinstance(polling_result.data, list):
                affected_records_accumulator.append(len(polling_result.data))
            else:
                # If it's a single response with count info, try to extract it
                affected_records_accumulator.append(1)

        elif polling_result.result_type == "attachment":
            # Erasure attachments might contain reports of what was deleted
            # For now, count as 1 affected record per attachment
            affected_records_accumulator.append(1)

        else:
            from fides.api.common_exceptions import PrivacyRequestError
            raise PrivacyRequestError(f"Unsupported erasure result type: {polling_result.result_type}")

    @classmethod
    def _add_attachment_metadata_to_rows(cls, db, attachment_id: str, rows: List[Row]) -> None:
        """Add attachment metadata to rows collection (like manual tasks do)."""
        from fides.api.models.attachment import Attachment

        attachment_record = (
            db.query(Attachment)
            .filter(Attachment.id == attachment_id)
            .first()
        )

        if attachment_record:
            try:
                size, url = attachment_record.retrieve_attachment()
                attachment_info = {
                    "file_name": attachment_record.file_name,
                    "download_url": str(url) if url else None,
                    "file_size": size,
                }
            except Exception as exc:
                logger.warning(
                    f"Could not retrieve attachment content for {attachment_record.file_name}: {exc}"
                )
                attachment_info = {
                    "file_name": attachment_record.file_name,
                    "download_url": None,
                    "file_size": None,
                }

            # Add attachment to the polling results
            attachments_item = None
            for item in rows:
                if isinstance(item, dict) and "attachments" in item:
                    attachments_item = item
                    break

            if attachments_item is None:
                attachments_item = {"attachments": []}
                rows.append(attachments_item)

            attachments_item["attachments"].append(attachment_info)


class PollingResponseProcessor:
    """
    Utility for processing async polling responses with smart data type inference.

    1. Infers data type from response characteristics
    2. Classifies whether response should be stored as attachment
    3. Processes response into appropriate result format
    """

    @classmethod
    def process_response(
        cls, response: Response, request_url: str, result_path: str = None
    ) -> PollingResult:
        """
        Process response with smart data type inference.

        Args:
            response: HTTP response object
            request_url: URL that was requested
            result_path: Optional path to extract data from JSON responses

        Returns:
            PollingResult with processed data
        """
        # Step 1: Infer data type
        inferred_type = cls._infer_data_type(response, request_url)

        # Step 2: Determine if this should be treated as an attachment
        if cls._should_store_as_attachment(response, inferred_type):
            # Step 3a: Build attachment result
            return cls._build_attachment_result(response, request_url, inferred_type)
        else:
            # Step 3b: Parse as structured data
            rows = cls._parse_to_rows(response, inferred_type, result_path)
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

    @classmethod
    def _infer_data_type(cls, response: Response, request_url: str) -> SupportedDataType:
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

    @classmethod
    def _should_store_as_attachment(
        cls, response: Response, inferred_type: SupportedDataType
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

    @classmethod
    def _extract_filename(cls, response: Response, request_url: str) -> str:
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

    @classmethod
    def _build_attachment_result(
        cls, response: Response, request_url: str, inferred_type: SupportedDataType
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
                "filename": cls._extract_filename(response, request_url),
                "size": len(response.content),
                "preserved_as_attachment": True,
            },
        )

    @classmethod
    def _parse_to_rows(
        cls, response: Response, data_type: SupportedDataType, result_path: str = None
    ) -> List[Row]:
        """
        Parse response to List[Row] based on data type.

        Note: This method is only called for responses that are NOT treated as attachments.
        """
        if data_type == SupportedDataType.json:
            return cls._parse_json_to_rows(response, result_path)
        elif data_type == SupportedDataType.csv:
            return cls._parse_csv_to_rows(response)
        elif data_type == SupportedDataType.xml:
            # Basic XML handling - could be enhanced
            raise PrivacyRequestError("XML parsing not yet implemented")
        else:
            raise PrivacyRequestError(f"Cannot parse {data_type} to rows")

    @classmethod
    def _parse_json_to_rows(cls, response: Response, result_path: str = None) -> List[Row]:
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
        elif isinstance(json_data, dict):
            return [json_data]
        else:
            raise PrivacyRequestError(
                f"Expected list or dict from result request, got: {type(json_data)}"
            )

    @classmethod
    def _parse_csv_to_rows(cls, response: Response) -> List[Row]:
        """Parse CSV response to List[Row]."""
        try:
            # Use pandas to parse CSV content
            csv_content = response.text
            df = pd.read_csv(io.StringIO(csv_content))

            # Convert to list of dictionaries
            return df.to_dict(orient='records')
        except Exception as e:
            raise PrivacyRequestError(f"Failed to parse CSV response: {e}")
