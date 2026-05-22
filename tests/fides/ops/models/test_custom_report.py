from typing import Generator

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.models.custom_report import CustomReport
from fides.api.models.fides_user import FidesUser
from fides.api.schemas.custom_report import CustomReportConfig, ReportType


class TestCustomReport:
    @pytest.fixture(scope="function")
    def custom_report(self, db: Session, user: FidesUser) -> Generator:
        custom_report = CustomReport.create(
            db=db,
            data={
                "name": "Custom report",
                "type": ReportType.datamap,
                "created_by": user.id,
                "config": CustomReportConfig(
                    column_map={
                        "system": {
                            "label": "Vendor",
                        },
                    }
                ).model_dump(mode="json"),
            },
        )
        yield custom_report
        custom_report.delete(db)

    def test_create_custom_report(self, db: Session, user: FidesUser):
        custom_report = CustomReport.create(
            db=db,
            data={
                "name": "Custom report",
                "type": ReportType.datamap,
                "created_by": user.id,
                "config": CustomReportConfig(
                    column_map={
                        "system": {
                            "label": "Vendor",
                        },
                    }
                ).model_dump(mode="json"),
            },
        )
        assert custom_report.name == "Custom report"
        assert custom_report.type == ReportType.datamap
        assert custom_report.created_by == user.id
        assert custom_report.config == {
            "column_map": {
                "system": {
                    "enabled": True,
                    "label": "Vendor",
                },
            },
            "table_state": {},
        }

    @pytest.mark.usefixtures("custom_report")
    def test_create_custom_report_duplicate_name(self, db: Session, user: FidesUser):
        with pytest.raises(KeyOrNameAlreadyExists) as exc:
            CustomReport.create(
                db=db,
                data={
                    "name": "Custom report",
                    "type": ReportType.datamap,
                    "created_by": user.id,
                    "config": CustomReportConfig(
                        column_map={
                            "system": {
                                "label": "Vendor",
                            },
                        }
                    ).model_dump(mode="json"),
                },
            )
        assert "Name Custom report already exists in CustomReport." in str(exc)

    @pytest.mark.usefixtures("custom_report")
    def test_update_custom_report(self, db: Session, user: FidesUser, custom_report):
        updated_report = custom_report.update(
            db=db,
            data={
                "config": CustomReportConfig(
                    column_map={
                        "system": {
                            "label": "System",
                        },
                    }
                ).model_dump(mode="json"),
            },
        )
        assert updated_report.name == "Custom report"
        assert updated_report.type == ReportType.datamap
        assert updated_report.created_by == user.id
        assert updated_report.config == {
            "column_map": {
                "system": {
                    "enabled": True,
                    "label": "System",
                },
            },
            "table_state": {},
        }

    @pytest.mark.usefixtures("custom_report")
    def test_update_custom_report_duplicate_name(self, db: Session, user: FidesUser):
        important_report = CustomReport.create(
            db=db,
            data={
                "name": "Important report",
                "type": ReportType.datamap,
                "created_by": user.id,
                "config": CustomReportConfig(
                    column_map={
                        "system": {
                            "label": "Vendor",
                        },
                    }
                ).model_dump(mode="json"),
            },
        )

        with pytest.raises(IntegrityError) as exc:
            important_report.update(
                db=db,
                data={"name": "Custom report"},
            )
        assert (
            'duplicate key value violates unique constraint "plus_custom_report_name_key"'
            in str(exc)
        )
