"""privacy_preference_v2

Revision ID: cff3f4e1669f
Revises: 848a8f4125cf
Create Date: 2023-12-06 02:42:38.041129

"""
import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "cff3f4e1669f"
down_revision = "848a8f4125cf"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "currentprivacypreferencev2",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "email",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "fides_user_device",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "phone_number",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("hashed_email", sa.String(), nullable=True),
        sa.Column("hashed_fides_user_device", sa.String(), nullable=True),
        sa.Column("hashed_phone_number", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("fides_string", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="last_saved_for_email"),
        sa.UniqueConstraint(
            "fides_user_device", name="last_saved_for_fides_user_device"
        ),
        sa.UniqueConstraint("phone_number", name="last_saved_for_phone_number"),
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_created_at"),
        "currentprivacypreferencev2",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_hashed_email"),
        "currentprivacypreferencev2",
        ["hashed_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_hashed_fides_user_device"),
        "currentprivacypreferencev2",
        ["hashed_fides_user_device"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_hashed_phone_number"),
        "currentprivacypreferencev2",
        ["hashed_phone_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_id"),
        "currentprivacypreferencev2",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_currentprivacypreferencev2_updated_at"),
        "currentprivacypreferencev2",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        "lastservednoticev2",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "email",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "fides_user_device",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "phone_number",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("hashed_email", sa.String(), nullable=True),
        sa.Column("hashed_fides_user_device", sa.String(), nullable=True),
        sa.Column("hashed_phone_number", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("served", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="last_served_for_email"),
        sa.UniqueConstraint(
            "fides_user_device", name="last_served_for_fides_user_device"
        ),
        sa.UniqueConstraint("phone_number", name="last_served_for_phone_number"),
    )
    op.create_index(
        op.f("ix_lastservednoticev2_created_at"),
        "lastservednoticev2",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednoticev2_hashed_email"),
        "lastservednoticev2",
        ["hashed_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednoticev2_hashed_fides_user_device"),
        "lastservednoticev2",
        ["hashed_fides_user_device"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednoticev2_hashed_phone_number"),
        "lastservednoticev2",
        ["hashed_phone_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lastservednoticev2_id"), "lastservednoticev2", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_lastservednoticev2_updated_at"),
        "lastservednoticev2",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        "servednoticehistoryv2",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "email",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "fides_user_device",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "phone_number",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("hashed_email", sa.String(), nullable=True),
        sa.Column("hashed_fides_user_device", sa.String(), nullable=True),
        sa.Column("hashed_phone_number", sa.String(), nullable=True),
        sa.Column(
            "anonymized_ip_address",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("notice_name", sa.String(), nullable=True),
        sa.Column("request_origin", sa.String(), nullable=True),
        sa.Column("url_recorded", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("user_geography", sa.String(), nullable=True),
        sa.Column("acknowledge_mode", sa.Boolean(), nullable=True),
        sa.Column("serving_component", sa.String(), nullable=True),
        sa.Column("served_notice_history_id", sa.String(), nullable=True),
        sa.Column("tcf_served", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("privacy_experience_config_history_id", sa.String(), nullable=True),
        sa.Column("privacy_experience_id", sa.String(), nullable=True),
        sa.Column("privacy_notice_history_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_experience_config_history_id"],
            ["privacyexperienceconfighistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_experience_id"],
            ["privacyexperience.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_notice_history_id"],
            ["privacynoticehistory.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_created_at"),
        "servednoticehistoryv2",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_hashed_email"),
        "servednoticehistoryv2",
        ["hashed_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_hashed_fides_user_device"),
        "servednoticehistoryv2",
        ["hashed_fides_user_device"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_hashed_phone_number"),
        "servednoticehistoryv2",
        ["hashed_phone_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_id"),
        "servednoticehistoryv2",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_notice_name"),
        "servednoticehistoryv2",
        ["notice_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_privacy_experience_config_history_id"),
        "servednoticehistoryv2",
        ["privacy_experience_config_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_privacy_experience_id"),
        "servednoticehistoryv2",
        ["privacy_experience_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_privacy_notice_history_id"),
        "servednoticehistoryv2",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_served_notice_history_id"),
        "servednoticehistoryv2",
        ["served_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_serving_component"),
        "servednoticehistoryv2",
        ["serving_component"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_updated_at"),
        "servednoticehistoryv2",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_servednoticehistoryv2_user_geography"),
        "servednoticehistoryv2",
        ["user_geography"],
        unique=False,
    )
    op.create_table(
        "privacypreferencehistoryv2",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column(
            "email",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "fides_user_device",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "phone_number",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("hashed_email", sa.String(), nullable=True),
        sa.Column("hashed_fides_user_device", sa.String(), nullable=True),
        sa.Column("hashed_phone_number", sa.String(), nullable=True),
        sa.Column(
            "anonymized_ip_address",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("notice_name", sa.String(), nullable=True),
        sa.Column("request_origin", sa.String(), nullable=True),
        sa.Column("url_recorded", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("user_geography", sa.String(), nullable=True),
        sa.Column(
            "affected_system_status",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=True,
        ),
        sa.Column("fides_string", sa.String(), nullable=True),
        sa.Column("method", sa.String(), nullable=True),
        sa.Column("preference", sa.String(), nullable=True),
        sa.Column("privacy_request_id", sa.String(), nullable=True),
        sa.Column(
            "secondary_user_ids",
            sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType(),
            nullable=True,
        ),
        sa.Column("served_notice_history_id", sa.String(), nullable=True),
        sa.Column(
            "tcf_preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("privacy_experience_config_history_id", sa.String(), nullable=True),
        sa.Column("privacy_experience_id", sa.String(), nullable=True),
        sa.Column("privacy_notice_history_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_experience_config_history_id"],
            ["privacyexperienceconfighistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_experience_id"],
            ["privacyexperience.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_notice_history_id"],
            ["privacynoticehistory.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_request_id"], ["privacyrequest.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_created_at"),
        "privacypreferencehistoryv2",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_hashed_email"),
        "privacypreferencehistoryv2",
        ["hashed_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_hashed_fides_user_device"),
        "privacypreferencehistoryv2",
        ["hashed_fides_user_device"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_hashed_phone_number"),
        "privacypreferencehistoryv2",
        ["hashed_phone_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_id"),
        "privacypreferencehistoryv2",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_notice_name"),
        "privacypreferencehistoryv2",
        ["notice_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_preference"),
        "privacypreferencehistoryv2",
        ["preference"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_privacy_experience_config_history_id"),
        "privacypreferencehistoryv2",
        ["privacy_experience_config_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_privacy_experience_id"),
        "privacypreferencehistoryv2",
        ["privacy_experience_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_privacy_notice_history_id"),
        "privacypreferencehistoryv2",
        ["privacy_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_privacy_request_id"),
        "privacypreferencehistoryv2",
        ["privacy_request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_served_notice_history_id"),
        "privacypreferencehistoryv2",
        ["served_notice_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_updated_at"),
        "privacypreferencehistoryv2",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacypreferencehistoryv2_user_geography"),
        "privacypreferencehistoryv2",
        ["user_geography"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_user_geography"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_updated_at"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_served_notice_history_id"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_privacy_request_id"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_privacy_notice_history_id"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_privacy_experience_id"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_privacy_experience_config_history_id"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_preference"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_notice_name"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_id"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_hashed_phone_number"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_hashed_fides_user_device"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_hashed_email"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_index(
        op.f("ix_privacypreferencehistoryv2_created_at"),
        table_name="privacypreferencehistoryv2",
    )
    op.drop_table("privacypreferencehistoryv2")
    op.drop_index(
        op.f("ix_servednoticehistoryv2_user_geography"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_updated_at"), table_name="servednoticehistoryv2"
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_serving_component"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_served_notice_history_id"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_privacy_notice_history_id"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_privacy_experience_id"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_privacy_experience_config_history_id"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_notice_name"), table_name="servednoticehistoryv2"
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_id"), table_name="servednoticehistoryv2"
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_hashed_phone_number"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_hashed_fides_user_device"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_hashed_email"),
        table_name="servednoticehistoryv2",
    )
    op.drop_index(
        op.f("ix_servednoticehistoryv2_created_at"), table_name="servednoticehistoryv2"
    )
    op.drop_table("servednoticehistoryv2")
    op.drop_index(
        op.f("ix_lastservednoticev2_updated_at"), table_name="lastservednoticev2"
    )
    op.drop_index(op.f("ix_lastservednoticev2_id"), table_name="lastservednoticev2")
    op.drop_index(
        op.f("ix_lastservednoticev2_hashed_phone_number"),
        table_name="lastservednoticev2",
    )
    op.drop_index(
        op.f("ix_lastservednoticev2_hashed_fides_user_device"),
        table_name="lastservednoticev2",
    )
    op.drop_index(
        op.f("ix_lastservednoticev2_hashed_email"), table_name="lastservednoticev2"
    )
    op.drop_index(
        op.f("ix_lastservednoticev2_created_at"), table_name="lastservednoticev2"
    )
    op.drop_table("lastservednoticev2")
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_updated_at"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_id"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_hashed_phone_number"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_hashed_fides_user_device"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_hashed_email"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_index(
        op.f("ix_currentprivacypreferencev2_created_at"),
        table_name="currentprivacypreferencev2",
    )
    op.drop_table("currentprivacypreferencev2")
