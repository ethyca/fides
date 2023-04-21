"""add privacy notice templates

Revision ID: d8a50048dfed
Revises: 8342453518cc
Create Date: 2023-04-20 18:47:50.905259

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.


revision = "d8a50048dfed"
down_revision = "8342453518cc"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "privacynoticetemplate",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("internal_description", sa.String(), nullable=True),
        sa.Column("regions", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("consent_mechanism", sa.String(), nullable=False),
        sa.Column("data_uses", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("enforcement_level", sa.String(), nullable=False),
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("has_gpc_flag", sa.Boolean(), nullable=False),
        sa.Column("displayed_in_privacy_center", sa.Boolean(), nullable=False),
        sa.Column("displayed_in_overlay", sa.Boolean(), nullable=False),
        sa.Column("displayed_in_api", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacynoticetemplate_id"),
        "privacynoticetemplate",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacynoticetemplate_regions"),
        "privacynoticetemplate",
        ["regions"],
        unique=False,
    )

    op.create_foreign_key(
        "privacynotice_origin_fkey",
        "privacynotice",
        "privacynoticetemplate",
        ["origin"],
        ["id"],
    )
    op.create_foreign_key(
        "privacynoticehistory_origin_fkey",
        "privacynoticehistory",
        "privacynoticetemplate",
        ["origin"],
        ["id"],
    )

    conn = op.get_bind()
    conn.execute("COMMIT")


def downgrade():
    op.drop_constraint(
        "privacynoticehistory_origin_fkey", "privacynoticehistory", type_="foreignkey"
    )
    op.drop_constraint("privacynotice_origin_fkey", "privacynotice", type_="foreignkey")
    op.drop_index(
        op.f("ix_privacynoticetemplate_regions"), table_name="privacynoticetemplate"
    )
    op.drop_index(
        op.f("ix_privacynoticetemplate_id"), table_name="privacynoticetemplate"
    )
    op.drop_table("privacynoticetemplate")
