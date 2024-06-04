"""property specific messaging db models

Revision ID: 2736c942faa2
Revises: efddde14da21
Create Date: 2024-05-28 14:26:09.012859

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2736c942faa2"
down_revision = "efddde14da21"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "messaging_template_to_property",
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
        sa.Column("messaging_template_id", sa.String(), nullable=False),
        sa.Column("property_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["messaging_template_id"],
            ["messaging_template.id"],
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["plus_property.id"],
        ),
        sa.PrimaryKeyConstraint("id", "messaging_template_id", "property_id"),
        sa.UniqueConstraint(
            "messaging_template_id",
            "property_id",
            name="messaging_template_id_property_id",
        ),
    )
    op.create_index(
        op.f("ix_messaging_template_to_property_id"),
        "messaging_template_to_property",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messaging_template_to_property_messaging_template_id"),
        "messaging_template_to_property",
        ["messaging_template_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_messaging_template_to_property_property_id"),
        "messaging_template_to_property",
        ["property_id"],
        unique=False,
    )
    op.add_column(
        "messaging_template", sa.Column("is_enabled", sa.Boolean(), nullable=True)
    )
    op.execute("UPDATE messaging_template SET is_enabled = FALSE;")

    op.alter_column("messaging_template", "is_enabled", nullable=False)

    op.alter_column("messaging_template", "key", new_column_name="type")

    op.drop_index(op.f("ix_messaging_template_key"), table_name="messaging_template")
    op.create_index(
        op.f("ix_messaging_template_type"), "messaging_template", ["type"], unique=False
    )
    op.add_column(
        "plus_property",
        sa.Column("is_default", sa.Boolean(), server_default="f", nullable=True),
    )
    op.create_index(
        "only_one_default",
        "plus_property",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "only_one_default",
        table_name="plus_property",
        postgresql_where=sa.text("is_default"),
    )
    op.drop_column("plus_property", "is_default")
    op.drop_index(op.f("ix_messaging_template_type"), table_name="messaging_template")
    op.alter_column("messaging_template", "type", new_column_name="key")
    op.create_index(
        "ix_messaging_template_key", "messaging_template", ["key"], unique=False
    )
    op.drop_column("messaging_template", "is_enabled")
    op.drop_index(
        op.f("ix_messaging_template_to_property_property_id"),
        table_name="messaging_template_to_property",
    )
    op.drop_index(
        op.f("ix_messaging_template_to_property_messaging_template_id"),
        table_name="messaging_template_to_property",
    )
    op.drop_index(
        op.f("ix_messaging_template_to_property_id"),
        table_name="messaging_template_to_property",
    )
    op.drop_table("messaging_template_to_property")
    # ### end Alembic commands ###
