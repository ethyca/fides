"""Schema for regulatory reporting templates

Adds:
- ``plus_custom_field_definition.system_managed`` — boolean flag that marks a
  field definition as platform-managed (e.g. seeded by the regulatory reporting
  templates reconciler). System-managed fields have their lifecycle controlled
  by that flow and are hidden from the standard custom-fields management UI.
- ``plus_custom_report.system_template_key`` — stable key (e.g. "ico", "dpc",
  "cnil") identifying the template that owns a system-managed CustomReport.
- ``plus_custom_report.location_code`` — fides location that gates the template
  (e.g. "gb", "ie", "fr"). Both columns are NULL for user-created reports.
- ``plus_reporting_template_custom_field`` — M:N association between system-
  managed CustomReports and the CustomFieldDefinitions they reference.

Revision ID: c8e9d3f7a2b4
Revises: d71c7d274c04
Create Date: 2026-04-22 16:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "c8e9d3f7a2b4"
down_revision = "d71c7d274c04"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "plus_custom_field_definition",
        sa.Column(
            "system_managed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "plus_custom_report",
        sa.Column("system_template_key", sa.String(), nullable=True),
    )
    op.add_column(
        "plus_custom_report",
        sa.Column("location_code", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_plus_custom_report_system_template_key",
        "plus_custom_report",
        ["system_template_key"],
    )
    op.create_index(
        "ix_plus_custom_report_location_code",
        "plus_custom_report",
        ["location_code"],
    )

    op.create_table(
        "plus_reporting_template_custom_field",
        sa.Column("custom_report_id", sa.String(), nullable=False),
        sa.Column("custom_field_definition_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["custom_report_id"], ["plus_custom_report.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["custom_field_definition_id"],
            ["plus_custom_field_definition.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("custom_report_id", "custom_field_definition_id"),
    )


def downgrade():
    op.drop_table("plus_reporting_template_custom_field")
    op.drop_index(
        "ix_plus_custom_report_location_code", table_name="plus_custom_report"
    )
    op.drop_index(
        "ix_plus_custom_report_system_template_key", table_name="plus_custom_report"
    )
    op.drop_column("plus_custom_report", "location_code")
    op.drop_column("plus_custom_report", "system_template_key")
    op.drop_column("plus_custom_field_definition", "system_managed")
