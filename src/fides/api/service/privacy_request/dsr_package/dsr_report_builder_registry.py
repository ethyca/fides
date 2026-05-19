"""Registry for the DSR report builder class and access review hooks.

Allows fidesplus (or other extensions) to replace the default DSRReportBuilder
with a custom implementation (e.g. AccessPackageReportBuilder) at startup,
and to register callbacks for the access review workflow.
"""

from io import BytesIO
from typing import Callable, Optional, Protocol, runtime_checkable

from sqlalchemy.orm import Session

from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DSRReportBuilder,
)


@runtime_checkable
class DSRReportBuilderProtocol(Protocol):
    """Contract for DSR report builders registered via this registry.

    The default DSRReportBuilder only implements generate() (HTML).
    Custom builders (e.g. AccessPackageReportBuilder) must implement
    all three format methods.
    """

    used_filenames_per_dataset: dict[str, set[str]]
    processed_attachments: dict[tuple[str, str], str]

    def generate(self) -> BytesIO: ...
    def generate_json(self) -> BytesIO: ...
    def generate_csv(self) -> BytesIO: ...


_dsr_report_builder_cls: type = DSRReportBuilder
_review_required: bool = False
_review_approved_callback: Optional[Callable[[str, Session], bool]] = None
_pre_restart_cleanup: Optional[Callable[[str, Session], None]] = None


def get_dsr_report_builder() -> type:
    """Return the current DSR report builder class."""
    return _dsr_report_builder_cls


def set_dsr_report_builder(cls: type[DSRReportBuilderProtocol]) -> None:
    """Replace the DSR report builder class used for package generation.

    Custom builders must satisfy DSRReportBuilderProtocol (generate,
    generate_json, generate_csv). The default DSRReportBuilder only
    implements generate() and is exempt — it never enters the custom
    builder branch in storage.py.
    """
    global _dsr_report_builder_cls
    _dsr_report_builder_cls = cls


def is_access_review_required() -> bool:
    """Whether access package review is required before delivery."""
    return _review_required


def set_access_review_required(required: bool) -> None:
    """Enable or disable access package review gate."""
    global _review_required
    _review_required = required


def get_review_approved_callback() -> Optional[Callable[[str, Session], bool]]:
    """Return the callback that checks whether a review has been approved.

    The callback receives (privacy_request_id, session) and returns True
    if the review is approved (i.e., the request should skip the gate).
    """
    return _review_approved_callback


def set_review_approved_callback(
    callback: Callable[[str, Session], bool] | None,
) -> None:
    """Register (or clear) a callback to check whether a review has been approved."""
    global _review_approved_callback
    _review_approved_callback = callback


def get_pre_restart_cleanup() -> Optional[Callable[[str, Session], None]]:
    """Return the callback that cleans up review state before a restart.

    The callback receives (privacy_request_id, session) and should delete
    the AccessPackageReview row so the request enters review fresh.
    """
    return _pre_restart_cleanup


def set_pre_restart_cleanup(callback: Callable[[str, Session], None] | None) -> None:
    """Register (or clear) a cleanup callback for access review state on restart."""
    global _pre_restart_cleanup
    _pre_restart_cleanup = callback
