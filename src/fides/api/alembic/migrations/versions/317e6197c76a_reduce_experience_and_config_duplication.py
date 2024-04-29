"""reduce experience and config duplication

Revision ID: 317e6197c76a
Revises: b8248ce6b8a1
Create Date: 2023-06-05 23:24:43.174826

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "317e6197c76a"
down_revision = "b8248ce6b8a1"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index(
        "ix_privacyexperiencehistory_experience_config_history_id",
        table_name="privacyexperiencehistory",
    )
    op.drop_index(
        "ix_privacyexperiencehistory_experience_config_id",
        table_name="privacyexperiencehistory",
    )
    op.drop_index(
        "ix_privacyexperiencehistory_id", table_name="privacyexperiencehistory"
    )
    op.drop_index(
        "ix_privacyexperiencehistory_privacy_experience_id",
        table_name="privacyexperiencehistory",
    )
    op.drop_index(
        "ix_privacyexperiencehistory_region", table_name="privacyexperiencehistory"
    )
    op.drop_constraint(
        "privacypreferencehistory_privacy_experience_history_id_fkey",
        "privacypreferencehistory",
        type_="foreignkey",
    )

    op.drop_table("privacyexperiencehistory")

    op.drop_index(
        "ix_privacyexperience_experience_config_history_id",
        table_name="privacyexperience",
    )
    op.drop_constraint(
        "privacyexperience_experience_config_history_id_fkey",
        "privacyexperience",
        type_="foreignkey",
    )

    op.drop_column("privacyexperience", "disabled")
    op.drop_column("privacyexperience", "version")
    op.drop_column("privacyexperience", "experience_config_history_id")

    op.drop_index(
        "ix_privacypreferencehistory_privacy_experience_history_id",
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "privacy_experience_history_id")

    op.add_column(
        "privacypreferencehistory",
        sa.Column("privacy_experience_id", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_privacy_experience_id"),
        "privacypreferencehistory",
        ["privacy_experience_id"],
        unique=False,
    )
    op.create_foreign_key(
        "privacypreferencehistory_privacy_experience_id_fkey",
        "privacypreferencehistory",
        "privacyexperience",
        ["privacy_experience_id"],
        ["id"],
    )
    # ### end Alembic commands ###


def downgrade():
    op.create_table(
        "privacyexperiencehistory",
        sa.Column("id", sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("disabled", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("component", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "version",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "privacy_experience_id", sa.VARCHAR(), autoincrement=False, nullable=False
        ),
        sa.Column("region", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column(
            "experience_config_id", sa.VARCHAR(), autoincrement=False, nullable=True
        ),
        sa.Column(
            "experience_config_history_id",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["experience_config_history_id"],
            ["privacyexperienceconfighistory.id"],
            name="privacyexperiencehistory_experience_config_history_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["experience_config_id"],
            ["privacyexperienceconfig.id"],
            name="privacyexperiencehistory_experience_config_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["privacy_experience_id"],
            ["privacyexperience.id"],
            name="privacyexperiencehistory_privacy_experience_id_fkey",
        ),
        sa.PrimaryKeyConstraint("id", name="privacyexperiencehistory_pkey"),
    )

    op.add_column(
        "privacypreferencehistory",
        sa.Column(
            "privacy_experience_history_id",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "privacypreferencehistory_privacy_experience_history_id_fkey",
        "privacypreferencehistory",
        "privacyexperiencehistory",
        ["privacy_experience_history_id"],
        ["id"],
    )

    op.drop_index(
        op.f("ix_privacypreferencehistory_privacy_experience_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_constraint(
        "privacypreferencehistory_privacy_experience_id_fkey",
        "privacypreferencehistory",
        type_="foreignkey",
    )
    op.drop_column("privacypreferencehistory", "privacy_experience_id")

    op.create_index(
        "ix_privacypreferencehistory_privacy_experience_history_id",
        "privacypreferencehistory",
        ["privacy_experience_history_id"],
        unique=False,
    )

    op.add_column(
        "privacyexperience",
        sa.Column(
            "experience_config_history_id",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "version",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "privacyexperience",
        sa.Column(
            "disabled",
            sa.BOOLEAN(),
            server_default="t",
            autoincrement=False,
            nullable=False,
        ),
    )
    op.create_foreign_key(
        "privacyexperience_experience_config_history_id_fkey",
        "privacyexperience",
        "privacyexperienceconfighistory",
        ["experience_config_history_id"],
        ["id"],
    )

    op.create_index(
        "ix_privacyexperience_experience_config_history_id",
        "privacyexperience",
        ["experience_config_history_id"],
        unique=False,
    )
    op.create_index(
        "ix_privacyexperiencehistory_region",
        "privacyexperiencehistory",
        ["region"],
        unique=False,
    )
    op.create_index(
        "ix_privacyexperiencehistory_privacy_experience_id",
        "privacyexperiencehistory",
        ["privacy_experience_id"],
        unique=False,
    )
    op.create_index(
        "ix_privacyexperiencehistory_id",
        "privacyexperiencehistory",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_privacyexperiencehistory_experience_config_id",
        "privacyexperiencehistory",
        ["experience_config_id"],
        unique=False,
    )
    op.create_index(
        "ix_privacyexperiencehistory_experience_config_history_id",
        "privacyexperiencehistory",
        ["experience_config_history_id"],
        unique=False,
    )
