"""data migration converting existing 'Cookies' resources to 'Asset' resources with type 'Cookie'

Revision ID: c9c72b3d550b
Revises: 9288f729cac4
Create Date: 2025-02-18 18:33:56.039924

"""

import uuid
from typing import Dict, Tuple

import sqlalchemy as sa
from alembic import op
from loguru import logger

from fides.api.models.asset import Asset

# revision identifiers, used by Alembic.
revision = "c9c72b3d550b"
down_revision = "9288f729cac4"
branch_labels = None
depends_on = None


def upgrade():
    # migrate existing cookies to assets
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT c.id, c.created_at, c.updated_at, c.name, c.domain, c.system_id, c.path, c.privacy_declaration_id, pd.system_id AS pud_system_id, pd.data_use "
            "FROM cookies c "
            "LEFT JOIN privacydeclaration pd ON c.privacy_declaration_id = pd.id"
        )
    )

    logger.debug("Converting existing cookies to assets")
    assets_to_create: Dict[str, Asset] = {}
    for row in result:
        if row.privacy_declaration_id is None:
            identifier = f"{row.name}_{row.system_id}"
            if identifier not in assets_to_create.keys():
                assets_to_create[identifier] = Asset(
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

        if row.pud_system_id:
            system_id = row.pud_system_id
            data_uses = [row.data_use]
        else:
            system_id = row.system_id
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
    assets_list = [
        {
            "id": asset.id if asset.id else str(uuid.uuid4()),
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
            "name": asset.name,
            "domain": asset.domain,
            "system_id": asset.system_id,
            "data_uses": asset.data_uses,
            "asset_type": "Cookie",
        }
        for asset in assets_to_create.values()
    ]

    if assets_list:
        logger.debug("Inserting assets into asset table ")
        connection.execute(
            sa.text(
                "INSERT INTO asset (id, created_at, updated_at, name, domain, system_id, data_uses, asset_type, with_consent) "
                "VALUES (:id, :created_at, :updated_at, :name, :domain, :system_id, :data_uses, :asset_type, false) "
                "ON CONFLICT DO NOTHING"
            ),
            assets_list,
        )
    else:
        logger.debug("No assets to insert into asset table. Skipping.")

    # Delete the cookies table
    logger.debug("Deleting cookies table")
    connection.execute(sa.text("DROP TABLE cookies"))


def downgrade():
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

    # fetch all privacy declarations
    privacy_declarations = connection.execute(
        sa.text("SELECT id, system_id, data_use FROM privacydeclaration")
    ).fetchall()
    # create a mapping of system_id and data_use to privacy_declaration_id
    privacy_declaration_mapping: Dict[Tuple[str, str], str] = {}
    for pud in privacy_declarations:
        privacy_declaration_mapping[(pud.system_id, pud.data_use)] = pud.id

    logger.debug("Migrating existing assets to cookies")
    for row in result:
        # Find the privacy declaration ID matching the system ID and data use
        privacy_declaration_ids = []
        for data_use in row.data_uses:
            pud_id = privacy_declaration_mapping.get((row.system_id, data_use), None)
            if pud_id:
                privacy_declaration_ids.append(pud_id)

        cookies_to_insert = []

        if len(privacy_declaration_ids) == 0:
            # If no privacy declaration match we attach to system_id
            cookies_to_insert.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "domain": row.domain,
                    "system_id": row.system_id,
                    "privacy_declaration_id": None,
                }
            )
        else:
            for privacy_declaration_id in privacy_declaration_ids:
                # Create a cookie for each privacy declaration ID
                # generate a new ID
                cookie_id = str(uuid.uuid4())
                cookies_to_insert.append(
                    {
                        "id": cookie_id,
                        "name": row.name,
                        "domain": row.domain,
                        "system_id": None,
                        "privacy_declaration_id": privacy_declaration_id,
                    }
                )

        if cookies_to_insert:
            connection.execute(
                sa.text(
                    "INSERT INTO cookies (id, created_at, updated_at, name, domain, system_id, privacy_declaration_id) "
                    "VALUES (:id, NOW(), NOW(), :name, :domain, :system_id, :privacy_declaration_id) "
                    "ON CONFLICT DO NOTHING"
                ),
                cookies_to_insert,
            )
