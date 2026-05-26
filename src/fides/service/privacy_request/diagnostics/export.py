"""
Export a non-PII diagnostics report as a ZIP file.
"""

import json
import zipfile
from io import BytesIO

from sqlalchemy.orm import Session

from fides.service.privacy_request.diagnostics.gather import (
    get_privacy_request_diagnostics,
)
from fides.service.privacy_request.diagnostics.schemas import (
    PrivacyRequestDiagnostics,
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


def build_diagnostics_zip(privacy_request_id: str, db: Session) -> BytesIO:
    """
    Gather diagnostics for a privacy request and return a ZIP file in memory.

    Raises PrivacyRequestNotFound if the privacy request does not exist.
    """
    diagnostics = get_privacy_request_diagnostics(privacy_request_id, db)
    return _serialize_diagnostics_to_zip(diagnostics)
