"""fidesops_user and client_detail

Revision ID: 5a966cd643d7
Revises: 1dfc5a2d30e7
Create Date: 2022-03-08 22:05:18.352032

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5a966cd643d7"
down_revision = "1dfc5a2d30e7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fidesopsuser",
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
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("salt", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_fidesopsuser_id"), "fidesopsuser", ["id"], unique=False)
    op.create_index(
        op.f("ix_fidesopsuser_username"), "fidesopsuser", ["username"], unique=True
    )
    op.add_column("client", sa.Column("fides_key", sa.String(), nullable=True))
    op.add_column("client", sa.Column("user_id", sa.String(), nullable=True))
    op.create_index(op.f("ix_client_fides_key"), "client", ["fides_key"], unique=True)
    op.create_unique_constraint("client_user_id_key", "client", ["user_id"])
    op.create_foreign_key(
        "client_user_id_fkey", "client", "fidesopsuser", ["user_id"], ["id"]
    )


def downgrade():
    op.drop_constraint("client_user_id_fkey", "client", type_="foreignkey")
    op.drop_constraint("client_user_id_key", "client", type_="unique")
    op.drop_index(op.f("ix_client_fides_key"), table_name="client")
    op.drop_column("client", "user_id")
    op.drop_column("client", "fides_key")
    op.drop_index(op.f("ix_fidesopsuser_username"), table_name="fidesopsuser")
    op.drop_index(op.f("ix_fidesopsuser_id"), table_name="fidesopsuser")
    op.drop_table("fidesopsuser")
