"""add datasetconfig.ctl_dataset_id fk

Adding a FK to datasetconfig pointing to the ctl_datasets table.
Also try to automigrate datasetconfig.datasets to the ctl_datasets row

Revision ID: 216cdc7944f1
Revises: 2fb48b0e268b
Create Date: 2022-12-09 22:03:51.097585

"""

import json
import uuid
from typing import Any, Dict

import sqlalchemy as sa
from alembic import op
from fideslang.models import Dataset
from sqlalchemy import text

# revision identifiers, used by Alembic.
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import TextClause

revision = "216cdc7944f1"
down_revision = "2fb48b0e268b"
branch_labels = None
depends_on = None

AUTO_MIGRATED_STRING = "auto-migrated from datasetconfig.dataset"


def upgrade():
    # Schema migration - add a nullable datasetconfig.ctl_dataset_id field.  We will shortly make it non-nullable.
    op.add_column(
        "datasetconfig", sa.Column("ctl_dataset_id", sa.String(), nullable=True)
    )
    op.create_index(
        op.f("ix_datasetconfig_ctl_dataset_id"),
        "datasetconfig",
        ["ctl_dataset_id"],
        unique=False,
    )
    op.create_foreign_key(
        "datasetconfig_ctl_dataset_id_fkey",
        "datasetconfig",
        "ctl_datasets",
        ["ctl_dataset_id"],
        ["id"],
    )

    # Data migration - automatically try to port datasetconfig.dataset -> ctl_datasets if possible.
    bind = op.get_bind()
    existing_datasetconfigs = bind.execute(
        text("SELECT id, created_at, updated_at, dataset FROM datasetconfig;")
    )
    for row in existing_datasetconfigs:
        dataset: Dict[str, Any] = row["dataset"]
        fides_key: str = dataset["fides_key"]

        insert_into_ctl_datasets_query: TextClause = text(
            "INSERT INTO ctl_datasets (id, fides_key, organization_fides_key, name, description, meta, data_categories, "
            "collections, data_qualifier, created_at, updated_at, joint_controller, retention, fides_meta, third_country_transfers, tags) "
            "VALUES (:id, :fides_key, :organization_fides_key, :name, :description, :meta, :data_categories, :collections, "
            ":data_qualifier, :created_at, :updated_at, :joint_controller, :retention, :fides_meta, :third_country_transfers, :tags)"
        )

        new_ctl_dataset_id: str = "ctl_" + str(uuid.uuid4())
        # Stashing extra text into the "meta" column so we can use this to downgrade if needed
        appended_meta: Dict = dataset.get("meta") or {}
        appended_meta["fides_source"] = AUTO_MIGRATED_STRING

        validated_dataset: Dict = Dataset(
            **dataset
        ).dict()  # Validating before we store.
        validated_dataset["id"] = new_ctl_dataset_id
        validated_dataset["fides_key"] = fides_key
        validated_dataset["collections"] = json.dumps(validated_dataset["collections"])
        validated_dataset["meta"] = json.dumps(appended_meta)
        validated_dataset["created_at"] = row["created_at"]
        validated_dataset["updated_at"] = row["updated_at"]
        validated_dataset["fides_meta"] = dataset.get("fides_meta") or dataset.get(
            "fidesops_meta"
        )

        try:
            bind.execute(
                insert_into_ctl_datasets_query,
                validated_dataset,
            )
        except IntegrityError as exc:
            raise Exception(
                f"Fides attempted to copy datasetconfig.datasets into their own ctl_datasets rows but got error: {exc}. "
                f"Adjust fides_keys in ctl_datasets table to not conflict."
            )

        update_dataset_config_query: TextClause = text(
            "UPDATE datasetconfig SET ctl_dataset_id= :new_ctl_dataset_id WHERE id= :datasetconfig_id"
        )

        bind.execute(
            update_dataset_config_query,
            {"new_ctl_dataset_id": new_ctl_dataset_id, "datasetconfig_id": row["id"]},
        )


def downgrade():
    # Reverse schema migration
    op.drop_constraint(
        "datasetconfig_ctl_dataset_id_fkey", "datasetconfig", type_="foreignkey"
    )
    op.drop_index(op.f("ix_datasetconfig_ctl_dataset_id"), table_name="datasetconfig")
    op.drop_column("datasetconfig", "ctl_dataset_id")

    # Reverse data migration: remove ctl_datasets that were automatically created by the forward migration
    bind = op.get_bind()
    remove_automigrated_ctl_datasets_query: TextClause = text(
        "DELETE FROM ctl_datasets WHERE meta->>'fides_source'= :automigration_string"
    )
    bind.execute(
        remove_automigrated_ctl_datasets_query,
        {"automigration_string": AUTO_MIGRATED_STRING},
    )
