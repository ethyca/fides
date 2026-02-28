import os
from collections import defaultdict
from enum import Enum as EnumType
from typing import Any, Callable, Optional
from urllib.parse import quote

from loguru import logger

from fides.api.util.storage_util import format_size

# This is the max file size for downloading the content of an attachment.
# This is an industry standard used by companies like Google and Microsoft.
LARGE_FILE_THRESHOLD = 2 * 1024 * 1024 * 1024  # 2 GB


class AllowedFileType(EnumType):
    """
    A class that contains the allowed file types and their MIME types.
    """

    pdf = "application/pdf"
    doc = "application/msword"
    docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    txt = "text/plain"
    jpg = "image/jpeg"
    jpeg = "image/jpeg"
    png = "image/png"
    xls = "application/vnd.ms-excel"
    xlsx = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    csv = "text/csv"
    zip = "application/zip"


LOCAL_FIDES_UPLOAD_DIRECTORY = "fides_uploads"


def get_local_filename(file_key: str) -> str:
    """Verifies that the local storage directory exists and returns the local filepath.

    This extra security checks are to prevent directory traversal attacks and "complete business and technical destruction".
    Thanks Claude.

    Args:
        file_key: The key/path for the file

    Returns:
        The full local filepath

    Raises:
        ValueError: If the file_key is invalid or would result in a path outside the upload directory
    """
    # Basic validation
    if not file_key:
        raise ValueError("File key cannot be empty")

    # Security checks before normalization
    if file_key.startswith("/"):
        raise ValueError("Invalid file key: cannot start with '/'")

    # Normalize the path to handle any path separators consistently
    # First normalize using os.path.normpath to handle any redundant separators
    normalized_key = os.path.normpath(file_key)
    # Then convert all separators to forward slashes for consistency
    normalized_key = normalized_key.replace("\\", "/")

    # Additional security: ensure the final path is within the upload directory
    final_path = os.path.join(LOCAL_FIDES_UPLOAD_DIRECTORY, normalized_key)
    if not os.path.abspath(final_path).startswith(
        os.path.abspath(LOCAL_FIDES_UPLOAD_DIRECTORY)
    ):
        raise ValueError(
            "Invalid file key: would result in path outside upload directory"
        )

    # Create all necessary directories
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    return final_path


def get_allowed_file_type_or_raise(file_key: str) -> str:
    """Verifies that the file type is allowed and returns the MIME type"""
    error_msg = f"Invalid or unallowed file extension: {file_key}"
    if "." not in file_key:
        logger.warning(f"File key {file_key} does not have a file extension")
        raise ValueError(error_msg)
    file_type = file_key.split(".")[-1]
    try:
        return AllowedFileType[file_type].value
    except KeyError:
        raise ValueError(error_msg)


def get_unique_filename(filename: str, used_filenames: set[str]) -> str:
    """
    Generates a unique filename by appending a counter if the file already exists.
    Tracks filenames per dataset to match DSR report builder behavior.

    Args:
        filename: The original filename
        used_filenames: Set of filenames that have already been used

    Returns:
        A unique filename that won't conflict with existing files in the same dataset
    """

    base_name, extension = os.path.splitext(filename)
    counter = 1
    unique_filename = filename

    # Check if file exists in this dataset's used_filenames set
    while unique_filename in used_filenames:
        unique_filename = f"{base_name}_{counter}{extension}"
        counter += 1
    return unique_filename


def determine_dataset_name_from_path(base_path: str) -> str:
    """
    Determine the dataset name from a base path.

    Args:
        base_path: The base path (e.g., "attachments", "data/manualtask/manual_data")

    Returns:
        The dataset name extracted from the path
    """
    if base_path == "attachments":
        return "attachments"

    # Extract dataset name from path like "data/manualtask/manual_data"
    path_parts = base_path.split("/")
    if len(path_parts) >= 2 and path_parts[0] == "data":
        return path_parts[1]  # e.g., "manualtask"

    return "unknown"


def resolve_attachment_storage_path(
    unique_filename: str,
    base_path: str,
) -> str:
    """
    Resolve the actual storage path for an attachment file.

    This function provides a single source of truth for how attachment files
    are stored in the ZIP file, ensuring consistency between DSR report builder
    and streaming storage components.

    Args:
        unique_filename: The unique filename for the attachment
        base_path: The base path for the attachment (e.g., "attachments", "data/dataset/collection")

    Returns:
        The full storage path for the attachment file
    """
    return f"{base_path}/{unique_filename}"


def generate_attachment_url_from_storage_path(
    download_url: str,
    unique_filename: str,
    base_path: str,
    html_directory: str,
    enable_streaming: bool = False,
) -> str:
    """
    Generate attachment URL based on the actual storage path and HTML template location.

    This is the CURRENTLY USED function for generating attachment URLs in DSR packages.
    It provides more sophisticated path resolution by:
    1. Using resolve_attachment_storage_path() to calculate the actual storage path
    2. Handling different directory structures (attachments vs data/dataset/collection)
    3. Generating proper relative paths from HTML template locations to attachment files
    4. URL-encoding filenames for proper HTML link functionality

    Used by:
    - _process_attachment_list() in this file
    - _write_attachment_content() in dsr_report_builder.py

    Args:
        download_url: The original download URL
        unique_filename: The unique filename for the attachment
        base_path: The base path where the attachment is stored (e.g., "attachments", "data/dataset/collection")
        html_directory: The directory where the HTML template is located
        enable_streaming: Whether streaming mode is enabled

    Returns:
        The appropriate attachment URL
    """
    if enable_streaming:
        # Calculate the actual storage path
        storage_path = resolve_attachment_storage_path(unique_filename, base_path)

        # URL-encode the filename for proper HTML link functionality
        # Always encode when streaming is enabled to ensure consistency
        encoded_filename = quote(unique_filename, safe="")

        # Generate relative path from HTML template directory to storage path
        if html_directory == "attachments" and base_path == "attachments":
            # From attachments/index.html to attachments/filename.pdf (same directory)
            return encoded_filename
        if html_directory.startswith("data/") and base_path.startswith("data/"):
            # From data/dataset/collection/index.html to data/dataset/collection/attachments/filename.pdf
            # Both are in data/ structure, so go to attachments subdirectory
            return f"attachments/{encoded_filename}"
        # For other cases, calculate relative path
        # This is a simplified approach - in practice, you might need more sophisticated path resolution
        return f"../{storage_path.replace(unique_filename, encoded_filename)}"
    return download_url


def process_attachment_naming(
    attachment: dict[str, Any],
    used_filenames: set[str],
    processed_attachments: dict[tuple[str, str], str],
    dataset_name: str = "attachments",
) -> Optional[tuple[str, tuple[str, str]]]:
    """
    Process attachment naming and return unique filename and attachment key.

    Args:
        attachment: The attachment dictionary
        used_filenames: Set of used filenames for this dataset
        processed_attachments: Dictionary mapping attachment keys to unique filenames
        dataset_name: The dataset name for context

    Returns:
        Tuple of (unique_filename, attachment_key) where attachment_key is (download_url, file_name)
    """
    file_name = attachment.get("file_name")
    download_url = attachment.get("download_url")

    if not file_name or not download_url:
        logger.warning(
            f"Skipping attachment with missing {'file name' if not file_name else 'download URL'}"
        )
        return None

    # Get or generate unique filename
    attachment_key = (download_url, file_name)
    if attachment_key not in processed_attachments:
        unique_filename = get_unique_filename(file_name, used_filenames)
        used_filenames.add(unique_filename)
        processed_attachments[attachment_key] = unique_filename
    else:
        unique_filename = processed_attachments[attachment_key]
        # Ensure the filename is also added to the current used_filenames set
        # to prevent conflicts in subsequent processing
        used_filenames.add(unique_filename)

    return (unique_filename, attachment_key)


def format_attachment_size(file_size: Any) -> str:
    """
    Format file size for display.

    Args:
        file_size: The file size (int, float, or other)

    Returns:
        Formatted file size string
    """
    return (
        format_size(float(file_size))
        if isinstance(file_size, (int, float))
        else "Unknown"
    )


def create_attachment_info_dict(
    attachment_url: str, file_size: str, file_name: str
) -> dict[str, str]:
    """
    Create attachment info dictionary for templates.

    Args:
        attachment_url: The attachment URL
        file_size: The formatted file size
        file_name: The original file name

    Returns:
        Dictionary with attachment information
    """
    # Always encode the URL for safe usage in templates
    safe_url = quote(attachment_url, safe="/:")

    return {
        "url": attachment_url,
        "safe_url": safe_url,
        "size": file_size,
        "original_name": file_name,
    }


def is_attachment_field(field_value: Any) -> bool:
    """
    Check if a field value contains attachment-like data.

    Args:
        field_value: The field value to check

    Returns:
        True if the field contains attachment-like data
    """
    if not isinstance(field_value, list) or not field_value:
        return False

    first_item = field_value[0]
    if not isinstance(first_item, dict):
        return False

    # Check if this field contains attachment-like data
    return all(key in first_item for key in ["file_name", "download_url", "file_size"])


def process_attachments_contextually(
    data: dict[str, Any],
    used_filenames_data: set[str],
    used_filenames_attachments: set[str],
    processed_attachments: dict[tuple[str, str], str],
    enable_streaming: bool = False,
    callback: Optional[Callable] = None,
) -> list[dict[str, Any]]:
    """
    Process attachments using the same contextual approach as DSR report builder.

    This function iterates through the data structure and processes attachments
    as they are encountered, maintaining the same logic as the DSR report builder.

    Args:
        data: The DSR data dictionary
        used_filenames_data: Set of used filenames for data datasets
        used_filenames_attachments: Set of used filenames for attachments
        processed_attachments: Dictionary mapping attachment keys to unique filenames
        enable_streaming: Whether streaming mode is enabled
        callback: Optional callback function to process each attachment
                 Signature: callback(attachment, unique_filename, attachment_info, context)

    Returns:
        List of processed attachment dictionaries with context information
    """
    processed_attachments_list = []

    # Process datasets (excluding attachments)
    datasets = _get_datasets_from_dsr_data(data)

    for dataset_name, collections in datasets.items():
        for collection_name, items in collections.items():
            for item in items:
                if not isinstance(item, dict):
                    continue

                # Process direct attachments in the item
                if "attachments" in item and isinstance(item["attachments"], list):
                    directory = f"data/{dataset_name}/{collection_name}"
                    processed = _process_attachment_list(
                        item["attachments"],
                        directory,
                        dataset_name,
                        used_filenames_data,
                        used_filenames_attachments,
                        processed_attachments,
                        enable_streaming,
                        callback,
                        {
                            "dataset": dataset_name,
                            "collection": collection_name,
                            "type": "direct",
                        },
                    )
                    processed_attachments_list.extend(processed)

                # Process nested attachment fields (ManualTask format)
                for field_name, field_value in item.items():
                    if is_attachment_field(field_value):
                        directory = f"data/{dataset_name}/{collection_name}"
                        processed = _process_attachment_list(
                            field_value,
                            directory,
                            dataset_name,
                            used_filenames_data,
                            used_filenames_attachments,
                            processed_attachments,
                            enable_streaming,
                            callback,
                            {
                                "dataset": dataset_name,
                                "collection": collection_name,
                                "field": field_name,
                                "type": "nested",
                            },
                        )
                        processed_attachments_list.extend(processed)

    # Process top-level attachments from the "attachments" key
    # These are legitimate top-level attachments, not duplicates of dataset attachments
    if "attachments" in data:
        processed = _process_attachment_list(
            data["attachments"],
            "attachments",
            "attachments",
            used_filenames_data,
            used_filenames_attachments,
            processed_attachments,
            enable_streaming,
            callback,
            {"type": "top_level"},
        )
        processed_attachments_list.extend(processed)

    return processed_attachments_list


def _get_datasets_from_dsr_data(dsr_data: dict[str, Any]) -> dict[str, Any]:
    """
    Extract datasets from DSR data using the same logic as DSR report builder.

    Args:
        dsr_data: The DSR data dictionary

    Returns:
        Dictionary of datasets with collections
    """

    datasets: dict[str, Any] = defaultdict(lambda: defaultdict(list))

    for key, rows in dsr_data.items():
        # Skip attachments - they're handled separately
        if key == "attachments":
            continue

        parts = key.split(":", 1)
        if len(parts) > 1:
            dataset_name, collection_name = parts
        else:
            # Try to determine dataset name from system_name in rows
            dataset_name = "manual"
            collection_name = parts[0]

            for row in rows:
                if isinstance(row, dict) and "system_name" in row:
                    dataset_name = row["system_name"]
                    break

        datasets[dataset_name][collection_name].extend(rows)

    return datasets


def _process_attachment_list(
    attachments: list[dict[str, Any]],
    directory: str,
    dataset_name: str,
    used_filenames_data: set[str],
    used_filenames_attachments: set[str],
    processed_attachments: dict[tuple[str, str], str],
    enable_streaming: bool,
    callback: Optional[Callable],
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Process a list of attachments using the same logic as DSR report builder.

    Args:
        attachments: List of attachment dictionaries
        directory: Directory path for the attachments
        dataset_name: Name of the dataset
        used_filenames_data: Set of used filenames for data datasets
        used_filenames_attachments: Set of used filenames for attachments
        processed_attachments: Dictionary mapping attachment keys to unique filenames
        enable_streaming: Whether streaming mode is enabled
        callback: Optional callback function to process each attachment
        context: Context information about where the attachment was found

    Returns:
        List of processed attachment dictionaries
    """
    processed_attachments_list = []

    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue

        # Get the appropriate used_filenames set based on dataset type
        used_filenames = (
            used_filenames_attachments
            if dataset_name == "attachments"
            else used_filenames_data
        )

        # Process attachment naming using shared utility
        result = process_attachment_naming(
            attachment, used_filenames, processed_attachments, dataset_name
        )

        if result is None:  # Skip if processing failed
            continue

        unique_filename, _ = result

        # Format file size using shared utility
        file_size = format_attachment_size(attachment.get("file_size"))

        # Generate attachment URL using shared utility with actual storage path
        download_url = attachment.get("download_url")
        if not download_url:
            continue

        attachment_url = generate_attachment_url_from_storage_path(
            download_url,
            unique_filename,
            directory,  # This is the base_path where the file will be stored
            directory,  # This is the HTML template directory
            enable_streaming,
        )

        # Create attachment info dictionary using shared utility
        file_name = attachment.get("file_name")
        if not file_name:
            continue

        attachment_info = create_attachment_info_dict(
            attachment_url, file_size, file_name
        )

        # Create processed attachment with context
        processed_attachment = {
            "attachment": attachment,
            "unique_filename": unique_filename,
            "attachment_info": attachment_info,
            "context": context,
            "directory": directory,
            "dataset_name": dataset_name,
        }

        # Call callback if provided
        if callback:
            callback(attachment, unique_filename, attachment_info, context)

        processed_attachments_list.append(processed_attachment)

    return processed_attachments_list


def resolve_path_from_context(
    attachment: dict[str, Any],
    default_path: str = "attachments",
) -> str:
    """
    Resolve the base path for an attachment based on its context.

    This function provides consistent base path resolution logic across
    different storage components.

    Args:
        attachment: The attachment dictionary
        default_path: Default path if no context is found

    Returns:
        The resolved path for the attachment
    """
    if not attachment.get("_context"):
        return default_path

    context = attachment["_context"]
    context_type = context.get("type")

    if context_type in ["direct", "nested"]:
        dataset = context.get("dataset", "")
        collection = context.get("collection", "")
        return f"data/{dataset}/{collection}/attachments"
    if context_type == "top_level":
        return "attachments"
    if context.get("key") and context.get("item_id"):
        return f"{context['key']}/{context['item_id']}/attachments"

    return default_path
