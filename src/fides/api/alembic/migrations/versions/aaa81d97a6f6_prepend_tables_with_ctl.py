"""prepend tables with ctl

Revision ID: aaa81d97a6f6
Revises: f53e04e5b7f5
Create Date: 2022-08-11 09:59:38.709501

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "aaa81d97a6f6"
down_revision = "f53e04e5b7f5"
branch_labels = None
depends_on = None


def upgrade():
    """Rename tables to avoid collisions with fidesops."""

    # Data Categories
    op.rename_table("data_categories", "ctl_data_categories")
    op.execute("ALTER INDEX data_categories_pkey RENAME TO ctl_data_categories_pkey")
    op.execute(
        "ALTER INDEX ix_data_categories_fides_key RENAME TO ix_ctl_data_categories_fides_key"
    )
    op.execute("ALTER INDEX ix_data_categories_id RENAME TO ix_ctl_data_categories_id")

    # Data Subjects
    op.rename_table("data_subjects", "ctl_data_subjects")
    op.execute("ALTER INDEX data_subjects_pkey RENAME TO ctl_data_subjects_pkey")
    op.execute(
        "ALTER INDEX ix_data_subjects_fides_key RENAME TO ix_ctl_data_subjects_fides_key"
    )
    op.execute("ALTER INDEX ix_data_subjects_id RENAME TO ix_ctl_data_subjects_id")

    # Data Uses
    op.rename_table("data_uses", "ctl_data_uses")
    op.execute("ALTER INDEX data_uses_pkey RENAME TO ctl_data_uses_pkey")
    op.execute(
        "ALTER INDEX ix_data_uses_fides_key RENAME TO ix_ctl_data_uses_fides_key"
    )
    op.execute("ALTER INDEX ix_data_uses_id RENAME TO ix_ctl_data_uses_id")

    # Data Qualifiers
    op.rename_table("data_qualifiers", "ctl_data_qualifiers")
    op.execute("ALTER INDEX data_qualifiers_pkey RENAME TO ctl_data_qualifiers_pkey")
    op.execute(
        "ALTER INDEX ix_data_qualifiers_fides_key RENAME TO ix_ctl_data_qualifiers_fides_key"
    )
    op.execute("ALTER INDEX ix_data_qualifiers_id RENAME TO ix_ctl_data_qualifiers_id")

    # Datasets
    op.rename_table("datasets", "ctl_datasets")
    op.execute("ALTER INDEX data_sets_pkey RENAME TO ctl_datasets_pkey")
    op.execute("ALTER INDEX ix_datasets_fides_key RENAME TO ix_ctl_datasets_fides_key")
    op.execute("ALTER INDEX ix_datasets_id RENAME TO ix_ctl_datasets_id")

    # Evaluations
    op.rename_table("evaluations", "ctl_evaluations")
    op.execute("ALTER INDEX evaluations_pkey RENAME TO ctl_evaluations_pkey")
    op.execute(
        "ALTER INDEX ix_evaluations_fides_key RENAME TO ix_ctl_evaluations_fides_key"
    )
    op.execute("ALTER INDEX ix_evaluations_id RENAME TO ix_ctl_evaluations_id")

    # Organizations
    op.rename_table("organizations", "ctl_organizations")
    op.execute("ALTER INDEX organizations_pkey RENAME TO ctl_organizations_pkey")
    op.execute(
        "ALTER INDEX ix_organizations_fides_key RENAME TO ix_ctl_organizations_fides_key"
    )
    op.execute("ALTER INDEX ix_organizations_id RENAME TO ix_ctl_organizations_id")

    # Policies
    op.rename_table("policies", "ctl_policies")
    op.execute("ALTER INDEX policies_pkey RENAME TO ctl_policies_pkey")
    op.execute("ALTER INDEX ix_policies_fides_key RENAME TO ix_ctl_policies_fides_key")
    op.execute("ALTER INDEX ix_policies_id RENAME TO ix_ctl_policies_id")

    # Registries
    op.rename_table("registries", "ctl_registries")
    op.execute("ALTER INDEX registries_pkey RENAME TO ctl_registries_pkey")
    op.execute(
        "ALTER INDEX ix_registries_fides_key RENAME TO ix_ctl_registries_fides_key"
    )
    op.execute("ALTER INDEX ix_registries_id RENAME TO ix_ctl_registries_id")

    # Systems
    op.rename_table("systems", "ctl_systems")
    op.execute("ALTER INDEX systems_pkey RENAME TO ctl_systems_pkey")
    op.execute("ALTER INDEX ix_systems_fides_key RENAME TO ix_ctl_systems_fides_key")
    op.execute("ALTER INDEX ix_systems_id RENAME TO ix_ctl_systems_id")


def downgrade():
    op.rename_table("ctl_data_categories", "data_categories")
    op.execute("ALTER INDEX ctl_data_categories_pkey RENAME TO data_categories_pkey")
    op.execute(
        "ALTER INDEX ix_ctl_data_categories_fides_key RENAME TO ix_data_categories_fides_key"
    )
    op.execute("ALTER INDEX ix_ctl_data_categories_id RENAME TO ix_data_categories_id")

    # Data Subjects
    op.rename_table("ctl_data_subjects", "data_subjects")
    op.execute("ALTER INDEX ctl_data_subjects_pkey RENAME TO data_subjects_pkey")
    op.execute(
        "ALTER INDEX ix_ctl_data_subjects_fides_key RENAME TO ix_data_subjects_fides_key"
    )
    op.execute("ALTER INDEX ix_ctl_data_subjects_id RENAME TO ix_data_subjects_id")

    # Data Uses
    op.rename_table("ctl_data_uses", "data_uses")
    op.execute("ALTER INDEX ctl_data_uses_pkey RENAME TO data_uses_pkey")
    op.execute(
        "ALTER INDEX ix_ctl_data_uses_fides_key RENAME TO ix_data_uses_fides_key"
    )
    op.execute("ALTER INDEX ix_ctl_data_uses_id RENAME TO ix_data_uses_id")

    # Data Qualifiers
    op.rename_table("ctl_data_qualifiers", "data_qualifiers")
    op.execute("ALTER INDEX ctl_data_qualifiers_pkey RENAME TO data_qualifiers_pkey")
    op.execute(
        "ALTER INDEX ix_ctl_data_qualifiers_fides_key RENAME TO ix_data_qualifiers_fides_key"
    )
    op.execute("ALTER INDEX ix_ctl_data_qualifiers_id RENAME TO ix_data_qualifiers_id")

    # Datasets
    op.rename_table("ctl_datasets", "datasets")
    op.execute("ALTER INDEX ctl_datasets_pkey RENAME TO datasets_pkey")
    op.execute("ALTER INDEX ix_ctl_datasets_fides_key RENAME TO ix_datasets_fides_key")
    op.execute("ALTER INDEX ix_ctl_datasets_id RENAME TO ix_datasets_id")

    # Evaluations
    op.rename_table("ctl_evaluations", "evaluations")
    op.execute("ALTER INDEX ctl_evaluations_pkey RENAME TO evaluations_pkey")
    op.execute(
        "ALTER INDEX ix_ctl_evaluations_fides_key RENAME TO ix_evaluations_fides_key"
    )
    op.execute("ALTER INDEX ix_ctl_evaluations_id RENAME TO ix_evaluations_id")

    # Organizations
    op.rename_table("ctl_organizations", "organizations")
    op.execute("ALTER INDEX ctl_organizations_pkey RENAME TO organizations_pkey")
    op.execute(
        "ALTER INDEX ix_ctl_organizations_fides_key RENAME TO ix_organizations_fides_key"
    )
    op.execute("ALTER INDEX ix_ctl_organizations_id RENAME TO ix_organizations_id")

    # Policies
    op.rename_table("ctl_policies", "policies")
    op.execute("ALTER INDEX ctl_policies_pkey RENAME TO policies_pkey")
    op.execute("ALTER INDEX ix_ctl_policies_fides_key RENAME TO ix_policies_fides_key")
    op.execute("ALTER INDEX ix_ctl_policies_id RENAME TO ix_policies_id")

    # Registries
    op.rename_table("ctl_registries", "registries")
    op.execute("ALTER INDEX ctl_registries_pkey RENAME TO registries_pkey")
    op.execute(
        "ALTER INDEX ix_ctl_registries_fides_key RENAME TO ix_registries_fides_key"
    )
    op.execute("ALTER INDEX ix_ctl_registries_id RENAME TO ix_registries_id")

    # Systems
    op.rename_table("ctl_systems", "systems")
    op.execute("ALTER INDEX ctl_systems_pkey RENAME TO systems_pkey")
    op.execute("ALTER INDEX ix_ctl_systems_fides_key RENAME TO ix_systems_fides_key")
    op.execute("ALTER INDEX ix_ctl_systems_id RENAME TO ix_systems_id")
