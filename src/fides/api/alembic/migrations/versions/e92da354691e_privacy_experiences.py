"""privacy experiences

Revision ID: e92da354691e
Revises: 5b03859e51b5
Create Date: 2023-04-24 14:49:37.588144

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e92da354691e"
down_revision = "5b03859e51b5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "privacyexperiencetemplate",
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
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("component", sa.String(), nullable=False),
        sa.Column("delivery_mechanism", sa.String(), nullable=False),
        sa.Column("regions", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("component_title", sa.String(), nullable=True),
        sa.Column("component_description", sa.String(), nullable=True),
        sa.Column("banner_title", sa.String(), nullable=True),
        sa.Column("banner_description", sa.String(), nullable=True),
        sa.Column("link_label", sa.String(), nullable=True),
        sa.Column("confirmation_button_label", sa.String(), nullable=True),
        sa.Column("reject_button_label", sa.String(), nullable=True),
        sa.Column("acknowledgement_button_label", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacyexperiencetemplate_id"),
        "privacyexperiencetemplate",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperiencetemplate_regions"),
        "privacyexperiencetemplate",
        ["regions"],
        unique=False,
    )
    op.create_table(
        "privacyexperience",
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
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("component", sa.String(), nullable=False),
        sa.Column("delivery_mechanism", sa.String(), nullable=False),
        sa.Column("regions", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("component_title", sa.String(), nullable=True),
        sa.Column("component_description", sa.String(), nullable=True),
        sa.Column("banner_title", sa.String(), nullable=True),
        sa.Column("banner_description", sa.String(), nullable=True),
        sa.Column("link_label", sa.String(), nullable=True),
        sa.Column("confirmation_button_label", sa.String(), nullable=True),
        sa.Column("reject_button_label", sa.String(), nullable=True),
        sa.Column("acknowledgement_button_label", sa.String(), nullable=True),
        sa.Column("version", sa.Float(), nullable=False),
        sa.Column("privacy_experience_template_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_experience_template_id"],
            ["privacyexperiencetemplate.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacyexperience_id"), "privacyexperience", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_privacyexperience_regions"),
        "privacyexperience",
        ["regions"],
        unique=False,
    )
    op.create_table(
        "privacyexperiencehistory",
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
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("component", sa.String(), nullable=False),
        sa.Column("delivery_mechanism", sa.String(), nullable=False),
        sa.Column("regions", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("component_title", sa.String(), nullable=True),
        sa.Column("component_description", sa.String(), nullable=True),
        sa.Column("banner_title", sa.String(), nullable=True),
        sa.Column("banner_description", sa.String(), nullable=True),
        sa.Column("link_label", sa.String(), nullable=True),
        sa.Column("confirmation_button_label", sa.String(), nullable=True),
        sa.Column("reject_button_label", sa.String(), nullable=True),
        sa.Column("acknowledgement_button_label", sa.String(), nullable=True),
        sa.Column("version", sa.Float(), nullable=False),
        sa.Column("privacy_experience_template_id", sa.String(), nullable=True),
        sa.Column("privacy_experience_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["privacy_experience_id"],
            ["privacyexperience.id"],
        ),
        sa.ForeignKeyConstraint(
            ["privacy_experience_template_id"],
            ["privacyexperiencetemplate.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_privacyexperiencehistory_id"),
        "privacyexperiencehistory",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_privacyexperiencehistory_regions"),
        "privacyexperiencehistory",
        ["regions"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_privacyexperiencehistory_regions"),
        table_name="privacyexperiencehistory",
    )
    op.drop_index(
        op.f("ix_privacyexperiencehistory_id"), table_name="privacyexperiencehistory"
    )
    op.drop_table("privacyexperiencehistory")
    op.drop_index(op.f("ix_privacyexperience_regions"), table_name="privacyexperience")
    op.drop_index(op.f("ix_privacyexperience_id"), table_name="privacyexperience")
    op.drop_table("privacyexperience")
    op.drop_index(
        op.f("ix_privacyexperiencetemplate_regions"),
        table_name="privacyexperiencetemplate",
    )
    op.drop_index(
        op.f("ix_privacyexperiencetemplate_id"), table_name="privacyexperiencetemplate"
    )
    op.drop_table("privacyexperiencetemplate")
