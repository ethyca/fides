"""update system.legal_basis_for_transfers

Revision ID: 3038667ba898
Revises: 507563f6f8d4
Create Date: 2023-08-25 14:19:16.798409

"""

from typing import Dict

import sqlalchemy as sa
from alembic import op
from loguru import logger
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "3038667ba898"
down_revision = "507563f6f8d4"
branch_labels = None
depends_on = None

legal_basis_transfers_upgrades: Dict[str, str] = {
    "Adequacy decision": "Adequacy Decision",
    "Standard contractual clauses": "SCCs",
    "Binding corporate rules": "BCRs",
}

legal_basis_transfers_downgrades: Dict[str, str] = {
    value: key for key, value in legal_basis_transfers_upgrades.items()
}


def upgrade():
    session = Session(bind=op.get_bind())
    conn = session.connection()
    bind = op.get_bind()

    #############################
    # legal_basis_for_transfers #
    #############################
    statement_transfers = text(
        """SELECT distinct legal_basis_for_transfers, id
FROM ctl_systems"""
    )
    existing_values_transfers = conn.execute(statement_transfers)

    # drop column since we will repopulating later
    op.drop_column(
        "ctl_systems",
        "legal_basis_for_transfers",
    )

    # add column back, but make it multi-value
    op.add_column(
        "ctl_systems",
        sa.Column(
            "legal_basis_for_transfers",
            type_=sa.ARRAY(sa.String()),
            server_default="{}",
            nullable=True,
        ),
    )

    # data migration - updates to some values since allowable values enum has changed
    # (enum is not enforced/specified on the DB, just API-level)

    for row in existing_values_transfers:
        existing_value = row[0]
        updated_value = legal_basis_transfers_upgrades.get(
            existing_value, existing_value
        )
        updated_value = (
            [updated_value] if updated_value else []
        )  # wrap in a list because column is now array type
        bind.execute(
            text(
                "UPDATE ctl_systems SET legal_basis_for_transfers = :updated_basis WHERE id = :id"
            ),
            {"updated_basis": updated_value, "id": row[1]},
        )

    #############################
    # legal_basis_for_profiling #
    #############################
    statement_profiling = text(
        """SELECT distinct legal_basis_for_profiling, id
FROM ctl_systems"""
    )
    existing_values_profiling = conn.execute(statement_profiling)

    op.drop_column(
        "ctl_systems",
        "legal_basis_for_profiling",
    )
    op.add_column(
        "ctl_systems",
        sa.Column(
            "legal_basis_for_profiling",
            type_=sa.ARRAY(sa.String()),
            server_default="{}",
            nullable=True,
        ),
    )

    # data migration - wrap values in a list
    for row in existing_values_profiling:
        existing_value = row[0]
        updated_value = legal_basis_transfers_upgrades.get(
            existing_value, existing_value
        )
        updated_value = (
            [updated_value] if updated_value else []
        )  # wrap in a list because column is now array type
        bind.execute(
            text(
                "UPDATE ctl_systems SET legal_basis_for_profiling = :updated_basis WHERE id = :id"
            ),
            {"updated_basis": updated_value, "id": row[1]},
        )


def downgrade():
    """
    Downgrade from array fields to single-value.

    We do not try to perform a data migration, since we'd likely have to
    drop some values arbitrarily. Better to just null the column out
    to make it clear that manual intervention is needed.
    """
    logger.warning(
        "Database migration downgrade will remove all values for `system.legal_basis_for_transfers` and `system.legal_basis_for_profiling` fields. \
        Values for these fields must be repopulated manually!"
    )
    op.drop_column(
        "ctl_systems",
        "legal_basis_for_transfers",
    )
    op.drop_column(
        "ctl_systems",
        "legal_basis_for_profiling",
    )

    op.add_column(
        "ctl_systems",
        sa.Column(
            "legal_basis_for_transfers",
            type_=sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        "ctl_systems",
        sa.Column(
            "legal_basis_for_profiling",
            type_=sa.String(),
            nullable=True,
        ),
    )
