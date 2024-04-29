"""add eu locations migration

Revision ID: d2996381c4dd
Revises: 2be84e68df32
Create Date: 2023-06-20 21:43:45.404454

"""

from typing import Dict, List, Optional

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
from sqlalchemy.engine import Connection, ResultProxy
from sqlalchemy.sql.elements import TextClause

revision = "d2996381c4dd"
down_revision = "2be84e68df32"
branch_labels = None
depends_on = None


region_map: Dict = {
    "eu_be": "be",
    "eu_bg": "bg",
    "eu_cz": "cz",
    "eu_dk": "dk",
    "eu_de": "de",
    "eu_ee": "ee",
    "eu_ie": "ie",
    "eu_el": "gr",
    "eu_es": "es",
    "eu_fr": "fr",
    "eu_hr": "hr",
    "eu_it": "it",
    "eu_cy": "cy",
    "eu_lv": "lv",
    "eu_lt": "lt",
    "eu_lu": "lu",
    "eu_hu": "hu",
    "eu_mt": "mt",
    "eu_nl": "nl",
    "eu_at": "at",
    "eu_pl": "pl",
    "eu_pt": "pt",
    "eu_ro": "ro",
    "eu_si": "si",
    "eu_sk": "sk",
    "eu_fi": "fi",
    "eu_se": "se",
    "isl": "is",
    "nor": "no",
}


def get_replacement_region(
    region: Optional[str], region_mapping: Dict[str, str]
) -> Optional[str]:
    """Get new region from region_mapping if it exists"""
    if not region:
        return region

    return region_mapping.get(region, region)


def upgrade_region_list(
    bind: Connection,
    select_query: TextClause,
    update_query: TextClause,
    region_mapping: Dict[str, str],
) -> None:
    """Upgrade regions for tables that have a "regions" list field"""
    existing_records: ResultProxy = bind.execute(select_query)
    for row in existing_records:
        regions: List[str] = row["regions"] or []
        regions_updated: bool = False
        for i, val in enumerate(regions):
            new_region = get_replacement_region(val, region_mapping)
            if val != new_region:
                regions_updated = True
                regions[i] = new_region

        if regions_updated:
            bind.execute(
                update_query,
                {"id": row["id"], "updated_regions": regions},
            )


def upgrade_region(
    bind: Connection,
    select_query: TextClause,
    update_query: TextClause,
    region_col_label: str,
    region_mapping: Dict[str, str],
):
    """Upgrade regions for tables that have a character varying field that stores a single region"""
    existing_records: ResultProxy = bind.execute(select_query)
    for row in existing_records:
        region: str = row[region_col_label]
        new_region = get_replacement_region(region, region_mapping)

        if region != new_region:
            bind.execute(
                update_query,
                {"id": row["id"], "updated_region": new_region},
            )


def migration_eu_regions(region_mapping: Dict[str, str]) -> None:
    """Generic migration that can upgrade or downgrade regions"""
    bind: Connection = op.get_bind()

    upgrade_region_list(
        bind,
        text("SELECT id, regions FROM privacynotice;"),
        text("UPDATE privacynotice SET regions = :updated_regions WHERE id= :id"),
        region_mapping,
    )

    upgrade_region_list(
        bind,
        text("SELECT id, regions FROM privacynoticetemplate;"),
        text(
            "UPDATE privacynoticetemplate SET regions = :updated_regions WHERE id= :id"
        ),
        region_mapping,
    )

    upgrade_region_list(
        bind,
        text("SELECT id, regions FROM privacynoticehistory;"),
        text(
            "UPDATE privacynoticehistory SET regions = :updated_regions WHERE id= :id"
        ),
        region_mapping,
    )

    upgrade_region(
        bind,
        text("SELECT id, region FROM privacyexperience;"),
        text("UPDATE privacyexperience SET region = :updated_region WHERE id= :id"),
        region_col_label="region",
        region_mapping=region_mapping,
    )

    upgrade_region(
        bind,
        text("SELECT id, user_geography FROM privacypreferencehistory;"),
        text(
            "UPDATE privacypreferencehistory SET user_geography = :updated_region WHERE id= :id"
        ),
        region_col_label="user_geography",
        region_mapping=region_mapping,
    )


def upgrade():
    migration_eu_regions(region_mapping=region_map)


def downgrade():
    migration_eu_regions(
        region_mapping={value: key for key, value in region_map.items()}
    )
