"""Add privacy preference history

Revision ID: ea84810271d7
Revises: ff782b0dc07e
Create Date: 2023-04-11 01:52:41.475314

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ea84810271d7"
down_revision = "ff782b0dc07e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "privacypreferencehistory",
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
        sa.Column(
            "affected_system_status",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column(
            "email",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("hashed_email", sa.String(), nullable=True),
        sa.Column("hashed_phone_number", sa.String(), nullable=True),
        sa.Column(
            "phone_number",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "preference",
            sa.Enum("opt_in", "opt_out", "acknowledge", name="userconsentpreference"),
            nullable=False,
        ),
        sa.Column("privacy_notice_history_id", sa.String(), nullable=False),
        sa.Column("privacy_request_id", sa.String(), nullable=True),
        sa.Column("provided_identity_id", sa.String(), nullable=True),
        sa.Column("relevant_systems", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("request_origin", sa.String(), nullable=True),
        sa.Column(
            "secondary_user_ids",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("url_recorded", sa.String(), nullable=True),
        sa.Column(
            "user_agent",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("user_geography", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_notice_history_id"],
            ["privacynoticehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_request_id"], ["privacyrequest.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_hashed_email"),
        "privacypreferencehistory",
        ["hashed_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_hashed_phone_number"),
        "privacypreferencehistory",
        ["hashed_phone_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_id"),
        "privacypreferencehistory",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_preference"),
        "privacypreferencehistory",
        ["preference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_privacy_notice_history_id"),
        "privacypreferencehistory",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_privacy_request_id"),
        "privacypreferencehistory",
        ["privacy_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_provided_identity_id"),
        "privacypreferencehistory",
        ["provided_identity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_user_geography"),
        "privacypreferencehistory",
        ["user_geography"],
        unique=False,
    )
    op.create_table(
        "currentprivacypreference",
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
        sa.Column(
            "preference",
            sa.Enum("opt_in", "opt_out", "acknowledge", name="userconsentpreference"),
            nullable=False,
        ),
        sa.Column("provided_identity_id", sa.String(), nullable=True),
        sa.Column("privacy_notice_id", sa.String(), nullable=False),
        sa.Column("privacy_notice_history_id", sa.String(), nullable=False),
        sa.Column("privacy_preference_history_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["privacy_notice_history_id"],
            ["privacynoticehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_notice_id"],
            ["privacynotice.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_preference_history_id"],
            ["privacypreferencehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["provided_identity_id"],
            ["providedidentity.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provided_identity_id", "privacy_notice_id", name="identity_privacy_notice"
        ),
    )
    op.create_index(
        op.f("ix_currentprivacypreference_id"),
        "currentprivacypreference",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_preference"),
        "currentprivacypreference",
        ["preference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_privacy_notice_history_id"),
        "currentprivacypreference",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_privacy_notice_id"),
        "currentprivacypreference",
        ["privacy_notice_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreference_privacy_preference_history_id"),
        "currentprivacypreference",
        ["privacy_preference_history_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_currentprivacypreference_privacy_preference_history_id"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_privacy_notice_id"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_privacy_notice_history_id"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_preference"),
        table_name="currentprivacypreference",
    )
    op.drop_index(
        op.f("ix_currentprivacypreference_id"), table_name="currentprivacypreference"
    )
    op.drop_table("currentprivacypreference")
    op.drop_index(
        op.f("ix_privacypreferencehistory_user_geography"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_provided_identity_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_privacy_request_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_privacy_notice_history_id"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_preference"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_id"), table_name="privacypreferencehistory"
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_hashed_phone_number"),
        table_name="privacypreferencehistory",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistory_hashed_email"),
        table_name="privacypreferencehistory",
    )
    op.drop_table("privacypreferencehistory")
    op.execute("drop type userconsentpreference")
