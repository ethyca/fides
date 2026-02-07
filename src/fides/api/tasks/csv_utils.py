import csv
import zipfile
from io import BytesIO, StringIO
from typing import Any, Optional

from fides.api.tasks.encryption_utils import encrypt_access_request_results
from fides.config import CONFIG


def create_csv_from_dict_list(data: list[dict[str, Any]]) -> BytesIO:
    """Create a CSV file from a list of dictionaries.

    Args:
        data: List of dictionaries to convert to CSV

    Returns:
        BytesIO: A file-like object containing the CSV data
    """
    if not data:
        return BytesIO()

    # Use StringIO to build CSV, then encode to BytesIO
    string_buffer = StringIO()

    # Get all unique keys from all dictionaries
    fieldnames = []
    for row in data:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    writer = csv.DictWriter(string_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

    # Convert to BytesIO with proper encoding
    buffer = BytesIO()
    buffer.write(string_buffer.getvalue().encode(CONFIG.security.encoding))
    buffer.seek(0)
    return buffer


def create_csv_from_normalized_dict(data: dict[str, Any]) -> BytesIO:
    """Create a CSV file from a single dictionary (flattened format).

    Args:
        data: Dictionary to convert to CSV

    Returns:
        BytesIO: A file-like object containing the CSV data
    """
    string_buffer = StringIO()

    # Flatten nested dictionaries with dot notation
    def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                # Convert lists and other non-primitive types to strings
                if isinstance(v, (list, tuple)):
                    items.append((new_key, str(v)))
                else:
                    items.append((new_key, v))
        return dict(items)

    flattened = flatten_dict(data)

    writer = csv.DictWriter(string_buffer, fieldnames=flattened.keys())
    writer.writeheader()
    writer.writerow(flattened)

    # Convert to BytesIO with proper encoding
    buffer = BytesIO()
    buffer.write(string_buffer.getvalue().encode(CONFIG.security.encoding))
    buffer.seek(0)
    return buffer


def create_attachment_csv(attachments: list[dict[str, Any]]) -> Optional[BytesIO]:
    """Create a CSV file containing attachment metadata.

    Args:
        attachments: List of attachment dictionaries

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

    return create_csv_from_dict_list(valid_attachments)


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
        buffer = create_csv_from_dict_list(items)
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
    buffer = create_csv_from_normalized_dict({key: value})
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
