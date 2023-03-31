"""Associate privacy notices with consent preferences

Revision ID: f9173fa62a91
Revises: 6d6b0b7cbb36
Create Date: 2023-03-30 18:46:42.670368

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f9173fa62a91"
down_revision = "6d6b0b7cbb36"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("consent", sa.Column("privacy_notice_id", sa.String(), nullable=True))
    op.add_column(
        "consent", sa.Column("privacy_notice_version", sa.Float(), nullable=True)
    )
    op.add_column(
        "consent", sa.Column("privacy_notice_history_id", sa.String(), nullable=True)
    )
    op.add_column(
        "consent",
        sa.Column(
            "user_geography",
            sa.String(),
            nullable=True,
        ),
    )
    op.alter_column("consent", "data_use", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column(
        "consent",
        "has_gpc_flag",
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default=sa.text("false"),
    )
    op.create_foreign_key(
        "consent_privacy_notice_history_id_fkey",
        "consent",
        "privacynoticehistory",
        ["privacy_notice_history_id"],
        ["id"],
    )
    op.create_foreign_key(
        "consent_privacy_notice_id_fkey",
        "consent",
        "privacynotice",
        ["privacy_notice_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uix_identity_privacy_notice_history",
        "consent",
        ["provided_identity_id", "privacy_notice_history_id"],
    )


def downgrade():
    op.drop_constraint(
        "consent_privacy_notice_history_id_fkey", "consent", type_="foreignkey"
    )
    op.drop_constraint("consent_privacy_notice_id_fkey", "consent", type_="foreignkey")
    op.alter_column(
        "consent",
        "has_gpc_flag",
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default=sa.text("false"),
    )
    op.alter_column("consent", "data_use", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_column("consent", "user_geography")
    op.drop_column("consent", "privacy_notice_history_id")
    op.drop_column("consent", "privacy_notice_version")
    op.drop_column("consent", "privacy_notice_id")
