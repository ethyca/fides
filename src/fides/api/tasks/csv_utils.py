import zipfile
from io import BytesIO
from typing import Any, Optional

import pandas as pd

from fides.api.tasks.encryption_utils import encrypt_access_request_results
from fides.config import CONFIG


def create_csv_from_dataframe(df: pd.DataFrame) -> BytesIO:
    """Create a CSV file from a pandas DataFrame.

    Args:
        df: The DataFrame to convert to CSV

    Returns:
        BytesIO: A file-like object containing the CSV data
    """
    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding=CONFIG.security.encoding)
    buffer.seek(0)
    return buffer


def create_attachment_csv(attachments: list[dict[str, Any]]) -> Optional[BytesIO]:
    """Create a CSV file containing attachment metadata.

    Args:
        attachments: List of attachment dictionaries
        privacy_request_id: The ID of the privacy request for encryption

    Returns:
        Optional[BytesIO]: A file-like object containing the CSV data, or None if no attachments
    """
    if not attachments:
        return None

    # Filter out invalid attachments and create a list of valid ones
    valid_attachments = []
    for a in attachments:
        if not isinstance(a, dict):
            continue

        # Check if the attachment has at least one of the required fields
        if not any(
            key in a
            for key in ["file_name", "file_size", "content_type", "download_url"]
        ):
            continue

        valid_attachments.append(
            {
                "file_name": a.get("file_name", ""),
                "file_size": a.get("file_size", 0),
                "content_type": a.get("content_type", "application/octet-stream"),
                "download_url": a.get("download_url", ""),
            }
        )

    # Return None if there are no valid attachments
    if not valid_attachments:
        return None

    df = pd.DataFrame(valid_attachments)

    if df.empty:
        return None

    return create_csv_from_dataframe(df)


def _write_attachment_csv(
    zip_file: zipfile.ZipFile,
    key: str,
    idx: int,
    attachments: list[dict[str, Any]],
    privacy_request_id: str,
) -> None:
    """Write attachment data to a CSV file in the zip archive.

    Args:
        zip_file: The zip file to write to
        key: The key for the data
        idx: The index of the item in the list
        attachments: List of attachment dictionaries
        privacy_request_id: The ID of the privacy request for encryption
    """
    buffer = create_attachment_csv(attachments)
    if buffer:
        zip_file.writestr(
            f"{key}/{idx + 1}/attachments.csv",
            encrypt_access_request_results(buffer.getvalue(), privacy_request_id),
        )


def _write_item_csv(
    zip_file: zipfile.ZipFile,
    key: str,
    items: list[dict[str, Any]],
    privacy_request_id: str,
) -> None:
    """Write item data to a CSV file in the zip archive.

    Args:
        zip_file: The zip file to write to
        key: The key for the data
        items: List of items to write
        privacy_request_id: The ID of the privacy request for encryption
    """
    if items:
        df = pd.DataFrame(items)
        buffer = create_csv_from_dataframe(df)
        zip_file.writestr(
            f"{key}.csv",
            encrypt_access_request_results(buffer.getvalue(), privacy_request_id),
        )


def _write_simple_csv(
    zip_file: zipfile.ZipFile,
    key: str,
    value: Any,
    privacy_request_id: str,
) -> None:
    """Write simple key-value data to a CSV file in the zip archive.

    Args:
        zip_file: The zip file to write to
        key: The key for the data
        value: The value to write
        privacy_request_id: The ID of the privacy request for encryption
    """
    df = pd.json_normalize({key: value})
    buffer = create_csv_from_dataframe(df)
    zip_file.writestr(
        f"{key}.csv",
        encrypt_access_request_results(buffer.getvalue(), privacy_request_id),
    )


def write_csv_to_zip(
    zip_file: zipfile.ZipFile, data: dict[str, Any], privacy_request_id: str
) -> None:
    """Write data to a zip file in CSV format.

    Args:
        zip_file: The zip file to write to
        data: The data to convert to CSV
        privacy_request_id: The ID of the privacy request for encryption
    """
    for key, value in data.items():
        if (
            isinstance(value, list)
            and value
            and all(isinstance(item, dict) for item in value)
        ):
            # Handle lists of dictionaries
            items: list[dict[str, Any]] = []
            for item in value:
                # Extract attachments if they exist
                attachments = item.pop("attachments", [])
                if attachments:
                    _write_attachment_csv(
                        zip_file, key, len(items), attachments, privacy_request_id
                    )
                items.append(item)
            _write_item_csv(zip_file, key, items, privacy_request_id)
        else:
            _write_simple_csv(zip_file, key, value, privacy_request_id)
