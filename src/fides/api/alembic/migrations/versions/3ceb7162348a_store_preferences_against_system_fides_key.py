"""store preferences against system id

Revision ID: 3ceb7162348a
Revises: 66df7d9b8103
Create Date: 2023-08-20 22:54:24.855291

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3ceb7162348a"
down_revision = "66df7d9b8103"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "currentprivacypreference",
        sa.Column("system_fides_key", sa.String(), nullable=True),
    )
    op.create_unique_constraint(
        "fides_user_device_identity_system_fides_key",
        "currentprivacypreference",
        ["fides_user_device_provided_identity_id", "system_fides_key"],
    )
    op.create_unique_constraint(
        "identity_system_fides_key",
        "currentprivacypreference",
        ["provided_identity_id", "system_fides_key"],
    )
    op.create_index(
        op.f("ix_currentprivacypreference_system_fides_key"),
        "currentprivacypreference",
        ["system_fides_key"],
        unique=False,
    )

    op.add_column(
        "lastservednotice", sa.Column("system_fides_key", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_lastservednotice_system_fides_key"),
        "lastservednotice",
        ["system_fides_key"],
        unique=False,
    )
    op.create_unique_constraint(
        "last_served_fides_user_device_identity_system_fides_key",
        "lastservednotice",
        ["fides_user_device_provided_identity_id", "system_fides_key"],
    )
    op.create_unique_constraint(
        "last_served_identity_system_fides_key",
        "lastservednotice",
        ["provided_identity_id", "system_fides_key"],
    )

    op.add_column(
        "privacypreferencehistory",
        sa.Column("system_fides_key", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_privacypreferencehistory_system_fides_key"),
        "privacypreferencehistory",
        ["system_fides_key"],
        unique=False,
    )

    op.add_column(
        "servednoticehistory", sa.Column("system_fides_key", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_servednoticehistory_system_fides_key"),
        "servednoticehistory",
        ["system_fides_key"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_servednoticehistory_system_fides_key"),
        table_name="servednoticehistory",
    )
    op.drop_column("servednoticehistory", "system_fides_key")
    op.drop_index(
        op.f("ix_privacypreferencehistory_system_fides_key"),
        table_name="privacypreferencehistory",
    )
    op.drop_column("privacypreferencehistory", "system_fides_key")
    op.drop_constraint(
        "last_served_identity_system_fides_key", "lastservednotice", type_="unique"
    )
    op.drop_constraint(
        "last_served_fides_user_device_identity_system_fides_key",
        "lastservednotice",
        type_="unique",
    )
    op.drop_index(
        op.f("ix_lastservednotice_system_fides_key"), table_name="lastservednotice"
    )
    op.drop_column("lastservednotice", "system_fides_key")
    op.drop_index(
        op.f("ix_currentprivacypreference_system_fides_key"),
        table_name="currentprivacypreference",
    )
    op.drop_constraint(
        "identity_system_fides_key", "currentprivacypreference", type_="unique"
    )
    op.drop_constraint(
        "fides_user_device_identity_system_fides_key",
        "currentprivacypreference",
        type_="unique",
    )
    op.drop_column("currentprivacypreference", "system_fides_key")
