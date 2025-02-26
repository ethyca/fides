"""data migration converting existing 'Cookies' resources to 'Asset' resources with type 'Cookie'

Revision ID: c9c72b3d550b
Revises: c961528edfc6
Create Date: 2025-02-18 18:33:56.039924

"""

import uuid
from typing import Dict

import psycopg2
import sqlalchemy as sa
from alembic import op
from loguru import logger

from fides.api.models.asset import Asset

# revision identifiers, used by Alembic.
revision = "c9c72b3d550b"
down_revision = "c961528edfc6"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.add_column("asset", sa.Column("description", sa.String(), nullable=True))
    except psycopg2.errors.DuplicateColumn:
        logger.warning(
            "Column 'description' already exists in 'asset' table. Skipping column addition."
        )

    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT id, created_at, updated_at, name, domain, system_id, path, privacy_declaration_id FROM cookies"
        )
    )

    logger.debug("Converting existing cookies to assets")
    assets_to_create: Dict[str, Asset] = {}
    for row in result:
        if row.privacy_declaration_id is None:
            # If the privacy declaration ID is None, we skip matching for this row
            assets_to_create[row.name] = Asset(
                id=str(uuid.uuid4()),
                created_at=row.created_at,
                updated_at=row.updated_at,
                name=row.name,
                domain=row.domain,
                system_id=row.system_id,
                data_uses=[],
                asset_type="Cookie",
            )
            continue
        pud_system_id_data_use = connection.execute(
            sa.text(
                "SELECT system_id, data_use FROM privacydeclaration WHERE id = :privacy_declaration_id"
            ),
            privacy_declaration_id=row.privacy_declaration_id,
        ).fetchone()

        if pud_system_id_data_use:
            pud_system_id, data_use = pud_system_id_data_use
        if pud_system_id:
            system_id = pud_system_id
        else:
            system_id = row.system_id
        if data_use:
            data_uses = [data_use]
        else:
            data_uses = []

        # Asset unique identifier is a composite of name, asset_type, domain, base_url, system_id. All assets here are cookies.
        identifier = f"{row.name}_{'Cookie'}_{row.domain}_{row.path}_{system_id}"
        if identifier in assets_to_create.keys():
            # If the asset already exists, append the data_use to the existing asset
            assets_to_create[identifier].data_uses.extend(data_uses)
        else:
            # If the asset does not exist, create a new asset with the data_use
            assets_to_create[identifier] = Asset(
                id=str(uuid.uuid4()),
                created_at=row.created_at,
                updated_at=row.updated_at,
                name=row.name,
                domain=row.domain,
                system_id=system_id,
                data_uses=data_uses,
                asset_type="Cookie",
            )

    # Insert the assets into the asset table
    logger.debug("Inserting assets into asset table ")
    for asset in assets_to_create.values():

        connection.execute(
            sa.text(
                "INSERT INTO asset (id, created_at, updated_at, name, domain, system_id, data_uses, asset_type, with_consent) "
                "VALUES (:id, :created_at, :updated_at, :name, :domain, :system_id, :data_uses, :asset_type, false) "
                "ON CONFLICT DO NOTHING"
            ),
            id=str(uuid.uuid4()),
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            name=asset.name,
            domain=asset.domain,
            system_id=asset.system_id,
            data_uses=asset.data_uses,
            asset_type="Cookie",
        )

    # Delete the cookies table
    logger.debug("Deleting cookies table")
    connection.execute(sa.text("DROP TABLE cookies"))


def downgrade():
    op.drop_column("asset", "description")

    # Recreate the cookies table
    logger.debug("Recreating cookies table")
    op.create_table(
        "cookies",
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
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=True),
        sa.Column("path", sa.String(), nullable=True),
        sa.Column("system_id", sa.String(), nullable=True),
        sa.Column("privacy_declaration_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["privacy_declaration_id"], ["privacydeclaration.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["system_id"], ["ctl_systems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name", "privacy_declaration_id", name="_cookie_name_privacy_declaration_uc"
        ),
    )
    op.create_index(op.f("ix_cookies_id"), "cookies", ["id"], unique=False)
    op.create_index(op.f("ix_cookies_name"), "cookies", ["name"], unique=False)
    op.create_index(
        op.f("ix_cookies_privacy_declaration_id"),
        "cookies",
        ["privacy_declaration_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cookies_system_id"), "cookies", ["system_id"], unique=False
    )
    # ### end Alembic commands ###

    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT id, name, domain, system_id, data_uses FROM asset WHERE asset_type = 'Cookie'"
        )
    )

    logger.debug("Migrating existing assets to cookies")
    for row in result:
        # Find the privacy declaration ID matching the system ID and data use
        privacy_declaration_ids = []
        for data_use in row.data_uses:
            pud = connection.execute(
                sa.text(
                    "SELECT id FROM privacydeclaration WHERE system_id = :system_id AND data_use = :data_use"
                ),
                system_id=row.system_id,
                data_use=data_use,
            ).fetchone()
            if pud:
                privacy_declaration_ids.append(pud.id)

        if len(privacy_declaration_ids) == 0:
            # If no privacy declaration match we attach to system_id
            connection.execute(
                sa.text(
                    "INSERT INTO cookies (id, created_at, updated_at, name, domain, system_id) "
                    "VALUES (:id, NOW(), NOW(), :name, :domain, :system_id)"
                    "ON CONFLICT DO NOTHING"
                ),
                id=cookie_id,
                name=row.name,
                domain=row.domain,
                system_id=row.system_id,
            )
        for privacy_declaration_id in privacy_declaration_ids:
            # Create a cookie for each privacy declaration ID
            # generate a new ID
            cookie_id = str(uuid.uuid4())
            connection.execute(
                sa.text(
                    "INSERT INTO cookies (id, created_at, updated_at, name, domain, privacy_declaration_id) "
                    "VALUES (:id, NOW(), NOW(), :name, :domain, :privacy_declaration_id)"
                    "ON CONFLICT DO NOTHING"
                ),
                id=cookie_id,
                name=row.name,
                domain=row.domain,
                privacy_declaration_id=privacy_declaration_id,
            )
