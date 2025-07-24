import json

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection


def requires_upgrade_migration(report):
    config = report.config
    column_map = config.get("column_map", {})

    for column in column_map.values():
        if isinstance(column, str):
            return True
    return False


def requires_downgrade_migration(report):
    config = report.config
    column_map = config.get("column_map", {})

    for column in column_map.values():
        if isinstance(column, dict):
            return True
    return False


def upgrade_custom_reports(connection: Connection):
    reports = connection.execute(sa.text("SELECT id, config FROM plus_custom_report"))

    for report in reports:
        config = report.config

        if not requires_upgrade_migration(report):
            continue

        column_map = config.get("column_map")
        table_state = config.get("table_state", {})
        column_visibility = table_state.get("columnVisibility", {})

        new_column_map = {
            key: {"label": value, "enabled": column_visibility.get(key, True)}
            for key, value in column_map.items()
        }

        config["column_map"] = new_column_map

        if "columnVisibility" in table_state:
            del table_state["columnVisibility"]

        connection.execute(
            sa.text("UPDATE plus_custom_report SET config = :config WHERE id = :id"),
            config=json.dumps(config),
            id=report.id,
        )


def downgrade_custom_reports(connection: Connection):
    reports = connection.execute(sa.text("SELECT id, config FROM plus_custom_report"))
    for report in reports:
        config = report.config

        if not requires_downgrade_migration(report):
            continue

        column_map = config.get("column_map")
        table_state = config.get("table_state", {})
        column_visibility = {key: value["enabled"] for key, value in column_map.items()}

        new_column_map = {key: value["label"] for key, value in column_map.items()}

        config["column_map"] = new_column_map
        table_state["columnVisibility"] = column_visibility

        connection.execute(
            sa.text("UPDATE plus_custom_report SET config = :config WHERE id = :id"),
            config=json.dumps(config),
            id=report.id,
        )
