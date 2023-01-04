"""add privacyrequest consent preferences and ruleuse table

Revision ID: de456534dbda
Revises: 1f61c765cd1c
Create Date: 2023-01-03 22:59:45.144538

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "de456534dbda"
down_revision = "1f61c765cd1c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ruleuse",
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
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("executable", sa.Boolean(), nullable=False),
        sa.Column("rule_id", sa.String(), nullable=False),
        sa.Column("client_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["client.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["rule.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ruleuse_id"), "ruleuse", ["id"], unique=False)
    op.create_index(op.f("ix_ruleuse_key"), "ruleuse", ["key"], unique=True)
    op.add_column(
        "privacyrequest",
        sa.Column(
            "consent_preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "consentrequest", sa.Column("privacy_request_id", sa.String(), nullable=True)
    )
    op.create_foreign_key(
        None, "consentrequest", "privacyrequest", ["privacy_request_id"], ["id"]
    )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("privacyrequest", "consent_preferences")
    op.drop_index(op.f("ix_ruleuse_key"), table_name="ruleuse")
    op.drop_index(op.f("ix_ruleuse_id"), table_name="ruleuse")
    op.drop_table("ruleuse")

    op.drop_constraint(None, "consentrequest", type_="foreignkey")
    op.drop_column("consentrequest", "privacy_request_id")
    # ### end Alembic commands ###
