"""table updates for user invite

Revision ID: 4d34d270f3ea
Revises: 956d21f13def
Create Date: 2024-02-01 00:50:46.547803

"""

import sqlalchemy as sa
from alembic import op
from citext import CIText

# revision identifiers, used by Alembic.
revision = "4d34d270f3ea"
down_revision = "956d21f13def"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("create type disabledreason as enum('pending_invite')")
    op.create_table(
        "fides_user_invite",
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
        sa.Column("username", CIText(), nullable=False),
        sa.Column("hashed_invite_code", sa.String(), nullable=False),
        sa.Column("salt", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["username"], ["fidesuser.username"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", "username"),
    )
    op.create_index(
        op.f("ix_fides_user_invite_id"), "fides_user_invite", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_fides_user_invite_username"),
        "fides_user_invite",
        ["username"],
        unique=False,
    )
    op.add_column("fidesuser", sa.Column("email_address", CIText(), nullable=True))
    op.add_column("fidesuser", sa.Column("disabled", sa.Boolean(), nullable=False))
    op.add_column(
        "fidesuser",
        sa.Column(
            "disabled_reason",
            sa.Enum("pending_invite", name="disabledreason"),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        "fidesuser_email_address", "fidesuser", ["email_address"]
    )


def downgrade():
    op.drop_constraint("fidesuser_email_address", "fidesuser", type_="unique")
    op.drop_column("fidesuser", "disabled_reason")
    op.drop_column("fidesuser", "disabled")
    op.drop_column("fidesuser", "email_address")
    op.drop_index(op.f("ix_fides_user_invite_username"), table_name="fides_user_invite")
    op.drop_index(op.f("ix_fides_user_invite_id"), table_name="fides_user_invite")
    op.drop_table("fides_user_invite")
    op.execute("drop type disabledreason")
