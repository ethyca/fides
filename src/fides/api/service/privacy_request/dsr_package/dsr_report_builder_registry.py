"""Registry for the DSR report builder class.

Allows fidesplus (or other extensions) to replace the default DSRReportBuilder
with a custom implementation (e.g. AccessPackageReportBuilder) at startup.
"""

from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DSRReportBuilder,
)

_dsr_report_builder_cls: type = DSRReportBuilder


def get_dsr_report_builder() -> type:
    """Return the current DSR report builder class."""
    return _dsr_report_builder_cls


def set_dsr_report_builder(cls: type) -> None:
    """Replace the DSR report builder class used for HTML package generation."""
    global _dsr_report_builder_cls
    _dsr_report_builder_cls = cls
