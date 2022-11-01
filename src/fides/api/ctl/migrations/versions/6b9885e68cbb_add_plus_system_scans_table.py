"""Add plus_system_scans table

Revision ID: 6b9885e68cbb
Revises: fb6b0150d6e4
Create Date: 2022-10-24 23:36:51.166480

"""
from alembic.op import create_table, drop_table
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, text

# revision identifiers, used by Alembic.
revision = "6b9885e68cbb"
down_revision = "fb6b0150d6e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    create_table(
        "plus_system_scans",
        Column("id", Integer(), primary_key=True),
        Column("created_at", DateTime(timezone=True), server_default=text("now()")),
        Column("error", String(), nullable=True),
        Column("is_classified", Boolean(), default=False, nullable=False),
        Column("result", JSON(), nullable=True),
        Column("status", String(), nullable=False),
        Column("system_count", Integer(), autoincrement=False, nullable=True),
        Column("updated_at", DateTime(timezone=True), server_default=text("now()")),
    )


def downgrade() -> None:
    drop_table("plus_system_scans")
