"""migrate meta vendor

Revision ID: 671358247251
Revises: ad2e3f9a6850
Create Date: 2023-09-13 20:52:58.425483

"""

import json
from typing import Dict, Optional

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
from sqlalchemy import text
from sqlalchemy.engine import Connection, ResultProxy
from sqlalchemy.sql.elements import TextClause

revision = "671358247251"
down_revision = "ad2e3f9a6850"
branch_labels = None
depends_on = None


def upgrade():
    """Migrate system > meta > vendor > id to system > vendor_id if applicable"""
    bind: Connection = op.get_bind()
    existing_systems: ResultProxy = bind.execute(
        text("select id, meta, vendor_id from ctl_systems;")
    )

    for row in existing_systems:
        if row["vendor_id"]:
            logger.warning(
                "Skipped migrating system > meta > vendor > id for system {} as vendor_id already exists",
                row["id"],
            )
            continue

        # Locate system > meta > vendor > id if it exists and is in correct format
        meta: Optional[Dict] = row["meta"] or {}
        if not isinstance(meta, dict):
            continue

        meta_vendor: Optional[Dict] = meta.get("vendor", {})
        meta_vendor_id: Optional[str] = (
            meta_vendor.get("id", None)
            if isinstance(meta_vendor, dict)
            else None  # Just double checking here
        )
        if not meta_vendor_id:
            continue

        # Migrate vendor_id, and remove "vendor" key from "meta" while we're here
        meta.pop("vendor")
        update_vendor_id_query: TextClause = text(
            "UPDATE ctl_systems SET vendor_id= :meta_vendor_id, meta=:updated_meta WHERE id= :id"
        )
        bind.execute(
            update_vendor_id_query,
            {
                "id": row["id"],
                "meta_vendor_id": str(meta_vendor_id),
                "updated_meta": json.dumps(meta),
            },
        )


def downgrade():
    """Migrate system > vendor_id to system > meta > vendor > id if applicable"""
    bind: Connection = op.get_bind()
    existing_systems: ResultProxy = bind.execute(
        text("select id, meta, vendor_id from ctl_systems;")
    )

    for row in existing_systems:
        existing_vendor_id: Optional[str] = row["vendor_id"]
        if not existing_vendor_id:
            continue

        meta: Dict = row["meta"] or {}
        if "vendor" not in meta:
            meta["vendor"] = {}
            meta["vendor"]["id"] = existing_vendor_id

        update_vendor_id_query: TextClause = text(
            "UPDATE ctl_systems SET meta = :updated_meta, vendor_id = null WHERE id= :id"
        )
        bind.execute(
            update_vendor_id_query,
            {"id": row["id"], "updated_meta": json.dumps(meta)},
        )
