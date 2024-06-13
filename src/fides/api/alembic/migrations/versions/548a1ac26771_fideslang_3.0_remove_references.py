"""remove data_qualifier

Revision ID: 548a1ac26771
Revises: 848a8f4125cf
Create Date: 2023-12-08 22:07:38.617038

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "548a1ac26771"
down_revision = "848a8f4125cf"
branch_labels = None
depends_on = None


def upgrade():
    ## Remove data qualifier references
    op.drop_index("ix_ctl_data_qualifiers_fides_key", table_name="ctl_data_qualifiers")
    op.drop_index("ix_ctl_data_qualifiers_id", table_name="ctl_data_qualifiers")
    op.drop_table("ctl_data_qualifiers")
    op.drop_column("ctl_datasets", "data_qualifier")
    op.drop_index("ix_ctl_systems_name", table_name="ctl_systems")
    op.drop_column("privacydeclaration", "data_qualifier")

    ## Remove registry references
    op.drop_index("ix_ctl_registries_fides_key", table_name="ctl_registries")
    op.drop_index("ix_ctl_registries_id", table_name="ctl_registries")
    op.drop_table("ctl_registries")
    op.drop_column("ctl_systems", "registry_id")

    ## Remove data use fields
    op.drop_column("ctl_data_uses", "legal_basis")
    op.drop_column("ctl_data_uses", "special_category")
    op.drop_column("ctl_data_uses", "legitimate_interest")
    op.drop_column("ctl_data_uses", "legitimate_interest_impact_assessment")
    op.drop_column("ctl_data_uses", "recipients")

    ## Remove dataset fields
    op.drop_column("ctl_datasets", "retention")
    op.drop_column("ctl_datasets", "joint_controller")
    op.drop_column("ctl_datasets", "third_country_transfers")

    ## Remove system fields
    op.drop_column("ctl_systems", "joint_controller")
    op.drop_column("ctl_systems", "data_responsibility_title")
    op.drop_column("ctl_systems", "third_country_transfers")
    op.drop_column("ctl_systems", "data_protection_impact_assessment")


def downgrade():
    ## Add back in data qualifier references
    op.add_column(
        "privacydeclaration",
        sa.Column("data_qualifier", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_index("ix_ctl_systems_name", "ctl_systems", ["name"], unique=False)
    op.add_column(
        "ctl_datasets",
        sa.Column("data_qualifier", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_table(
        "ctl_data_qualifiers",
        sa.Column("id", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("fides_key", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "organization_fides_key", sa.TEXT(), autoincrement=False, nullable=True
        ),
        sa.Column("name", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("description", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("parent_key", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "tags", postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True
        ),
        sa.Column("is_default", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column(
            "active",
            sa.BOOLEAN(),
            server_default=sa.text("true"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("version_added", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("version_deprecated", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("replaced_by", sa.TEXT(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="ctl_data_qualifiers_pkey"),
    )
    op.create_index(
        "ix_ctl_data_qualifiers_id", "ctl_data_qualifiers", ["id"], unique=False
    )
    op.create_index(
        "ix_ctl_data_qualifiers_fides_key",
        "ctl_data_qualifiers",
        ["fides_key"],
        unique=False,
    )

    ## Add back in registry references
    op.add_column(
        "ctl_systems",
        sa.Column("registry_id", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.create_table(
        "ctl_registries",
        sa.Column("id", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column("fides_key", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "organization_fides_key", sa.TEXT(), autoincrement=False, nullable=True
        ),
        sa.Column("name", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("description", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "tags", postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True
        ),
        sa.PrimaryKeyConstraint("id", name="ctl_registries_pkey"),
    )
    op.create_index("ix_ctl_registries_id", "ctl_registries", ["id"], unique=False)
    op.create_index(
        "ix_ctl_registries_fides_key", "ctl_registries", ["fides_key"], unique=False
    )

    ## Add back system fields
    op.add_column(
        "ctl_systems",
        sa.Column(
            "data_protection_impact_assessment",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ctl_systems",
        sa.Column(
            "third_country_transfers",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ctl_systems",
        sa.Column(
            "data_responsibility_title",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ctl_systems",
        sa.Column(
            "joint_controller", postgresql.BYTEA(), autoincrement=False, nullable=True
        ),
    )

    ## Add back dataset fields
    op.add_column(
        "ctl_datasets",
        sa.Column(
            "third_country_transfers",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ctl_datasets",
        sa.Column(
            "joint_controller", postgresql.BYTEA(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "ctl_datasets",
        sa.Column("retention", sa.VARCHAR(), autoincrement=False, nullable=True),
    )

    ## Add back data use fields
    op.add_column(
        "ctl_data_uses",
        sa.Column(
            "recipients",
            postgresql.ARRAY(sa.VARCHAR()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ctl_data_uses",
        sa.Column(
            "legitimate_interest_impact_assessment",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "ctl_data_uses",
        sa.Column(
            "legitimate_interest", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "ctl_data_uses",
        sa.Column("special_category", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "ctl_data_uses",
        sa.Column("legal_basis", sa.TEXT(), autoincrement=False, nullable=True),
    )
