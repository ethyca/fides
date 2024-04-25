"""tcf_purpose_overrides

Revision ID: 848a8f4125cf
Revises: 7f7c2b098f5d
Create Date: 2023-12-02 13:18:55.768697

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "848a8f4125cf"
down_revision = "7f7c2b098f5d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tcf_purpose_overrides",
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
        sa.Column("purpose", sa.Integer(), nullable=False),
        sa.Column("is_included", sa.Boolean(), server_default="t", nullable=True),
        sa.Column("required_legal_basis", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tcf_purpose_overrides_id"),
        "tcf_purpose_overrides",
        ["id"],
        unique=False,
    )
    op.create_unique_constraint(
        "purpose_constraint", "tcf_purpose_overrides", ["purpose"]
    )

    op.create_index(
        op.f("ix_tcf_purpose_overrides_purpose"),
        "tcf_purpose_overrides",
        ["purpose"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_tcf_purpose_overrides_purpose"), table_name="tcf_purpose_overrides"
    )
    op.drop_index(
        op.f("ix_tcf_purpose_overrides_id"), table_name="tcf_purpose_overrides"
    )
    op.drop_table("tcf_purpose_overrides")
