import zipfile
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import ActionType
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from fides.api.service.privacy_request.dsr_package.dsr_report_builder import (
    DsrReportBuilder,
)


@pytest.fixture
def dsr_data() -> dict:
    """Sample DSR data for testing"""
    return {
        "dataset1:collection1": [
            {"id": 1, "name": "Item 1", "email": "item1@example.com"},
            {"id": 2, "name": "Item 2", "email": "item2@example.com"},
        ],
        "dataset2:collection1": [
            {"id": 3, "name": "Item 3", "email": "item3@example.com"},
        ],
        "manual:collection1": [
            {"id": 4, "name": "Item 4", "email": "item4@example.com"},
        ],
    }


class TestDsrReportBuilder:
    def test_generate_report_structure(self, privacy_request, dsr_data: dict):
        """Test that the generated report has the correct structure"""
        builder = DsrReportBuilder(privacy_request, dsr_data)
        report = builder.generate()

        # Verify it's a valid zip file
        with zipfile.ZipFile(report) as zip_file:
            # Check for required files
            assert "welcome.html" in zip_file.namelist()
            assert "data/main.css" in zip_file.namelist()
            assert "data/back.svg" in zip_file.namelist()

            # Check dataset structure
            assert "data/dataset1/index.html" in zip_file.namelist()
            assert "data/dataset2/index.html" in zip_file.namelist()
            assert "data/manual/index.html" in zip_file.namelist()

            # Check collection structure
            assert "data/dataset1/collection1/index.html" in zip_file.namelist()
            assert "data/dataset1/collection1/1.html" in zip_file.namelist()
            assert "data/dataset1/collection1/2.html" in zip_file.namelist()

    def test_report_content(self, privacy_request, dsr_data: dict):
        """Test that the report content is correctly formatted"""
        builder = DsrReportBuilder(privacy_request, dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(report) as zip_file:
            # Check welcome page content
            welcome_content = zip_file.read("welcome.html").decode("utf-8")
            assert "DSR Report" in welcome_content
            assert "dataset1" in welcome_content

            # Check dataset index content
            dataset1_content = zip_file.read("data/dataset1/index.html").decode("utf-8")
            assert "dataset1" in dataset1_content
            assert "collection1" in dataset1_content

            # Check collection index content
            collection1_content = zip_file.read(
                "data/dataset1/collection1/index.html"
            ).decode("utf-8")
            assert "collection1" in collection1_content
            assert "item #1" in collection1_content
            assert "item #2" in collection1_content

            # Check individual item content
            item1_content = zip_file.read("data/dataset1/collection1/1.html").decode(
                "utf-8"
            )
            assert "collection1 (item #1)" in item1_content
            assert "item1@example.com" in item1_content
            assert "Item 1" in item1_content

    def test_empty_dsr_data(self, privacy_request):
        """Test report generation with empty DSR data"""
        builder = DsrReportBuilder(privacy_request, {})
        report = builder.generate()

        with zipfile.ZipFile(report) as zip_file:
            assert "welcome.html" in zip_file.namelist()
            assert "data/main.css" in zip_file.namelist()
            assert "data/back.svg" in zip_file.namelist()
            # Should not have any dataset directories
            assert not any(
                name.startswith("data/")
                and name != "data/main.css"
                and name != "data/back.svg"
                for name in zip_file.namelist()
            )

    def test_privacy_request_mapping(self, privacy_request, dsr_data: dict):
        """Test that privacy request data is correctly mapped in the report"""
        builder = DsrReportBuilder(privacy_request, dsr_data)
        report = builder.generate()

        with zipfile.ZipFile(report) as zip_file:
            welcome_content = zip_file.read("welcome.html").decode("utf-8")
            assert str(privacy_request.id) in welcome_content
            assert privacy_request.policy.get_action_type().value in welcome_content
            assert (
                privacy_request.requested_at.strftime("%m/%d/%Y %H:%M %Z")
                in welcome_content
            )
