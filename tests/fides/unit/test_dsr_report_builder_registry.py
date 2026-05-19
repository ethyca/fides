"""Tests for dsr_report_builder_registry defaults and set/get behavior."""

from io import BytesIO

import pytest

from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    BaseDSRReportBuilder,
    DSRReportBuilder,
)
from fides.api.service.privacy_request.dsr_package.dsr_report_builder_registry import (
    get_dsr_report_builder,
    get_pre_restart_cleanup,
    get_review_approved_callback,
    is_access_review_required,
    set_access_review_required,
    set_dsr_report_builder,
    set_pre_restart_cleanup,
    set_review_approved_callback,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset all registry state after each test."""
    yield
    set_dsr_report_builder(DSRReportBuilder)
    set_access_review_required(False)
    set_review_approved_callback(None)
    set_pre_restart_cleanup(None)


class TestBuilderRegistry:
    def test_default_builder_is_dsr_report_builder(self):
        assert get_dsr_report_builder() is DSRReportBuilder

    def test_set_and_get_builder(self):
        class FakeBuilder(BaseDSRReportBuilder):
            used_filenames_per_dataset: dict = {}
            processed_attachments: dict = {}

            def generate(self) -> BytesIO:
                return BytesIO()

            def generate_json(self) -> BytesIO:
                return BytesIO()

            def generate_csv(self) -> BytesIO:
                return BytesIO()

        set_dsr_report_builder(FakeBuilder)
        assert get_dsr_report_builder() is FakeBuilder


class TestReviewRequired:
    def test_default_is_false(self):
        assert is_access_review_required() is False

    def test_set_and_get(self):
        set_access_review_required(True)
        assert is_access_review_required() is True


def _approved_callback(pr_id: str, session: object) -> bool:
    return pr_id == "approved-id"


def _cleanup_callback(pr_id: str, session: object) -> None:
    pass


class TestCallbackRegistry:
    """Both callback slots follow the same get/set pattern."""

    @pytest.mark.parametrize(
        "getter,setter,callback",
        [
            (
                get_review_approved_callback,
                set_review_approved_callback,
                _approved_callback,
            ),
            (get_pre_restart_cleanup, set_pre_restart_cleanup, _cleanup_callback),
        ],
        ids=["review_approved", "pre_restart_cleanup"],
    )
    def test_default_is_none(self, getter, setter, callback):
        assert getter() is None

    @pytest.mark.parametrize(
        "getter,setter,callback",
        [
            (
                get_review_approved_callback,
                set_review_approved_callback,
                _approved_callback,
            ),
            (get_pre_restart_cleanup, set_pre_restart_cleanup, _cleanup_callback),
        ],
        ids=["review_approved", "pre_restart_cleanup"],
    )
    def test_set_and_get(self, getter, setter, callback):
        setter(callback)
        assert getter() is callback

    def test_approved_callback_returns_expected_values(self):
        """Verify the approved callback is actually invoked, not just stored."""
        set_review_approved_callback(_approved_callback)
        callback = get_review_approved_callback()
        assert callback("approved-id", None) is True
        assert callback("other-id", None) is False
