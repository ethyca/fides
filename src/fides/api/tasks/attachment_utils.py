from io import BytesIO
from typing import Any, Optional

import pandas as pd

from fides.config import CONFIG


def remove_attachment_content(obj: Any) -> None:
    """Recursively remove content from attachments in any nested structure.

    Args:
        obj: The object to process. Can be a dict, list, or any other type.
    """
    if isinstance(obj, dict):
        if "attachments" in obj and isinstance(obj["attachments"], list):
            for attachment in obj["attachments"]:
                if isinstance(attachment, dict) and "content" in attachment:
                    attachment.pop("content")
        for value in obj.values():
            remove_attachment_content(value)
    elif isinstance(obj, list):
        for item in obj:
            remove_attachment_content(item)


def create_attachment_csv(
    attachments: list[dict[str, Any]], privacy_request_id: str
) -> Optional[BytesIO]:
    """Create a CSV file containing attachment metadata.

    Args:
        attachments: List of attachment dictionaries
        privacy_request_id: The ID of the privacy request for encryption

    Returns:
        Optional[BytesIO]: A file-like object containing the CSV data, or None if no attachments
    """
    if not attachments:
        return None

    df = pd.DataFrame(
        [
            {
                "file_name": a.get("file_name", ""),
                "file_size": a.get("file_size", 0),
                "content_type": a.get("content_type", "application/octet-stream"),
                "download_url": a.get("download_url", ""),
            }
            for a in attachments
            if isinstance(a, dict)
        ]
    )

    if df.empty:
        return None

    buffer = BytesIO()
    df.to_csv(buffer, index=False, encoding=CONFIG.security.encoding)
    buffer.seek(0)
    return buffer
