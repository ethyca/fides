"""
Export a non-PII diagnostics report as a ZIP file to configured storage.
"""

import json
import secrets
import zipfile
from datetime import datetime, timezone
from io import BytesIO

from sqlalchemy.orm import Session

from fides.api.models.storage import get_active_default_storage_config
from fides.api.schemas.storage.storage import StorageType
from fides.api.service.storage import StorageProviderFactory
from fides.config import CONFIG
from fides.service.privacy_request.diagnostics.exceptions import (
    DefaultStorageNotConfiguredError,
)
from fides.service.privacy_request.diagnostics.gather import (
    get_privacy_request_diagnostics,
)
from fides.service.privacy_request.diagnostics.schemas import (
    PrivacyRequestDiagnostics,
    PrivacyRequestDiagnosticsExportResponse,
)

PRIVACY_REQUEST_DIAGNOSTICS_PREFIX = "privacy-request-diagnostics"


def _build_diagnostics_object_key(privacy_request_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rand = secrets.token_hex(4)
    return (
        f"{PRIVACY_REQUEST_DIAGNOSTICS_PREFIX}/"
        f"{privacy_request_id}/"
        f"{timestamp}-{rand}.zip"
    )


def _serialize_diagnostics_to_zip(diagnostics: PrivacyRequestDiagnostics) -> BytesIO:
    """Serialize diagnostics payload into a ZIP file held in memory."""
    data = diagnostics.model_dump(mode="json")
    json_bytes = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")

    buf = BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("diagnostics.json", json_bytes)
    buf.seek(0)
    return buf


def export_privacy_request_diagnostics(
    privacy_request_id: str, db: Session
) -> PrivacyRequestDiagnosticsExportResponse:
    """
    Export a non-PII diagnostics report as a ZIP file to configured storage
    and return a downloadable URL (signed/presigned where applicable).
    """
    storage_config = get_active_default_storage_config(db)
    if not storage_config:
        raise DefaultStorageNotConfiguredError(
            "No default storage backend is configured. "
            "Configure a storage destination via the application settings API "
            "before exporting diagnostics."
        )

    provider = StorageProviderFactory.create(storage_config)
    bucket = StorageProviderFactory.get_bucket_from_config(storage_config)

    storage_type = (
        storage_config.type
        if isinstance(storage_config.type, StorageType)
        else StorageType(storage_config.type)
    )

    diagnostics = get_privacy_request_diagnostics(privacy_request_id, db)
    buf = _serialize_diagnostics_to_zip(diagnostics)
    object_key = _build_diagnostics_object_key(privacy_request_id)

    provider.upload(
        bucket=bucket,
        key=object_key,
        data=buf,
        content_type="application/zip",
    )

    download_url = provider.generate_presigned_url(
        bucket=bucket,
        key=object_key,
        ttl_seconds=CONFIG.security.subject_request_download_link_ttl_seconds,
    )

    return PrivacyRequestDiagnosticsExportResponse(
        download_url=str(download_url),
        storage_type=storage_type.value,
        object_key=object_key,
        created_at=datetime.now(timezone.utc),
    )
