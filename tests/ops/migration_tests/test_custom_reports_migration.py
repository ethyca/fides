import json

import pytest

from fides.api.alembic.migrations.helpers.custom_report_migration_functions import (
    downgrade_custom_reports,
    upgrade_custom_reports,
)
from fides.api.alembic.migrations.helpers.database_functions import generate_record_id
from fides.api.schemas.custom_report import ReportType


class TestCustomReportyMigrationFunctions:

    def test_upgrade_custom_reports(self, db):
        db.execute(
            "INSERT INTO plus_custom_report (id, type, config) VALUES (:id, :type, :config)",
            {
                "id": generate_record_id("rep"),
                "type": ReportType.datamap,
                "config": json.dumps(
                    {
                        "column_map": {
                            "system": "Vendor",
                        },
                        "table_state": {
                            "filters": {},
                            "groupBy": "system, data_use",
                            "columnOrder": [],
                            "columnVisibility": {
                                "system": True,
                            },
                        },
                    }
                ),
            },
        )
        db.commit()

        upgrade_custom_reports(db.connection())

        report = db.execute("SELECT * FROM plus_custom_report").fetchone()
        assert report.config == {
            "column_map": {
                "system": {
                    "label": "Vendor",
                    "enabled": True,
                },
            },
            "table_state": {
                "filters": {},
                "groupBy": "system, data_use",
                "columnOrder": [],
            },
        }

    def test_downgrade_custom_reports(self, db):
        db.execute(
            "INSERT INTO plus_custom_report (id, type, config) VALUES (:id, :type, :config)",
            {
                "id": generate_record_id("rep"),
                "type": ReportType.datamap,
                "config": json.dumps(
                    {
                        "column_map": {
                            "system": {
                                "label": "Vendor",
                                "enabled": True,
                            },
                        },
                        "table_state": {
                            "filters": {},
                            "groupBy": "system, data_use",
                            "columnOrder": [],
                        },
                    }
                ),
            },
        )
        db.commit()

        downgrade_custom_reports(db.connection())

        report = db.execute("SELECT * FROM plus_custom_report").fetchone()
        assert report.config == {
            "column_map": {
                "system": "Vendor",
            },
            "table_state": {
                "filters": {},
                "groupBy": "system, data_use",
                "columnOrder": [],
                "columnVisibility": {
                    "system": True,
                },
            },
        }
