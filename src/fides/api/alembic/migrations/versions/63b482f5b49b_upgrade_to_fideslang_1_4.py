"""Upgrade to fideslang 1.4

Revision ID: 63b482f5b49b
Revises: deb97d9393f3
Create Date: 2023-05-26 07:51:25.947974

"""

import json
from typing import Dict, List, Optional

from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import Connection, ResultProxy
from sqlalchemy.sql.elements import TextClause

# revision identifiers, used by Alembic.
revision = "63b482f5b49b"
down_revision = "deb97d9393f3"
branch_labels = None
depends_on = None

# The `key` is the old value, the `value` is the new value
data_use_upgrades: Dict[str, str] = {
    "third_party_sharing.payment_processing": "essential.service.payment_processing",
    "third_party_sharing.fraud_detection": "essential.service.fraud_detection",
    "advertising": "marketing.advertising",
    "advertising.first_party": "marketing.advertising.first_party",
    "advertising.first_party.contextual": "marketing.advertising.first_party.contextual",
    "advertising.first_party.personalized": "marketing.advertising.first_party.targeted",
    "advertising.third_party": "marketing.advertising.third_party.targeted",
    "advertising.third_party.personalized": "marketing.advertising.third_party.targeted",
    "third_party_sharing.personalized_advertising": "marketing.advertising.third_party.targeted",
    "provide": "essential",
    "provide.service": "essential.service",
}
data_use_downgrades: Dict[str, str] = {
    value: key for key, value in data_use_upgrades.items()
}


def update_privacy_declaration_data_uses(
    bind: Connection, data_use_map: Dict[str, str]
):
    """Upgrade or downgrade data uses from fideslang 1.4 for privacy declarations"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, data_use FROM privacydeclaration;")
    )
    for row in existing_ctl_policies:
        data_use: str = row["data_use"]
        updated_data_use: Optional[str] = data_use_map.get(data_use, None)

        if updated_data_use:
            update_data_use_query: TextClause = text(
                "UPDATE privacydeclaration SET data_use = :updated_use WHERE id= :declaration_id"
            )
            bind.execute(
                update_data_use_query,
                {"declaration_id": row["id"], "updated_use": updated_data_use},
            )


def update_ctl_policy_data_uses(bind: Connection, data_use_map: Dict[str, str]):
    """Upgrade or downgrade data uses from fideslang 1.4 for ctl policies"""
    existing_ctl_policies: ResultProxy = bind.execute(
        text("SELECT id, rules FROM ctl_policies;")
    )
    for row in existing_ctl_policies:
        needs_update: bool = False
        rules: List[Dict] = row["rules"]
        for i, rule in enumerate(rules or []):
            data_uses: Dict = rule.get("data_uses", {})
            for j, val in enumerate(data_uses.get("values", [])):
                new_data_use: Optional[str] = data_use_map.get(val, None)
                if new_data_use:
                    rules[i]["data_uses"]["values"][j] = new_data_use
                    needs_update = True

        if needs_update:
            update_data_use_query: TextClause = text(
                "UPDATE ctl_policies SET rules = :updated_rules WHERE id= :policy_id"
            )
            bind.execute(
                update_data_use_query,
                {"policy_id": row["id"], "updated_rules": json.dumps(rules)},
            )


def upgrade() -> None:
    bind: Connection = op.get_bind()

    logger.info("Upgrading data use on privacy declaration")
    update_privacy_declaration_data_uses(bind, data_use_upgrades)

    logger.info("Upgrading ctl policy rule data uses")
    update_ctl_policy_data_uses(bind, data_use_upgrades)


def downgrade():
    bind: Connection = op.get_bind()

    logger.info("Downgrading data use on privacy declaration")
    update_privacy_declaration_data_uses(bind, data_use_downgrades)

    logger.info("Downgrading ctl policy rule data uses")
    update_ctl_policy_data_uses(bind, data_use_downgrades)
