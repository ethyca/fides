"""data migration converting existing 'Cookies' resources to 'Asset' resources with type 'Cookie'

Revision ID: c9c72b3d550b
Revises: c961528edfc6
Create Date: 2025-02-18 18:33:56.039924

"""

<<<<<<< HEAD
=======
import uuid
from typing import Dict, List, Tuple

import psycopg2
import sqlalchemy as sa
>>>>>>> 54e4eac93 (no n+1 queries)
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = "c9c72b3d550b"
down_revision = "c961528edfc6"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT c.id, c.created_at, c.updated_at, c.name, c.domain, c.system_id, c.path, c.privacy_declaration_id, pd.system_id AS pud_system_id, pd.data_use "
            "FROM cookies c "
            "LEFT JOIN privacydeclaration pd ON c.privacy_declaration_id = pd.id"
        )
    )

    for row in result:
<<<<<<< HEAD
        data_use_result = connection.execute(
            sa.text(
                "SELECT data_use FROM privacydeclaration WHERE id = :privacy_declaration_id"
            ),
            privacy_declaration_id=row.privacy_declaration_id,
        ).fetchone()

        data_uses = [data_use_result.data_use] if data_use_result else []
=======
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
    logger.debug("Inserting assets into asset table ")
    for asset in assets_to_create.values():
>>>>>>> 54e4eac93 (no n+1 queries)

        connection.execute(
            sa.text(
                "INSERT INTO asset (id, created_at, updated_at, name, domain, system_id, data_uses, asset_type, with_consent) "
                "VALUES (:id, :created_at, :updated_at, :name, :domain, :system_id, :data_uses, :asset_type, false)"
            ),
            id=str(uuid.uuid4()),
            created_at=row.created_at,
            updated_at=row.updated_at,
            name=row.name,
            domain=row.domain,
            system_id=row.system_id,
            data_uses=data_uses,
            asset_type="Cookie",
        )

    op.add_column("asset", sa.Column("description", sa.String(), nullable=True))


def downgrade():
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            "SELECT id, created_at, updated_at, name, domain, system_id, locations, data_uses FROM asset WHERE asset_type = 'Cookie'"
        )
    )

<<<<<<< HEAD
    for row in result:
        connection.execute(
            sa.text(
                "INSERT INTO cookies (id, created_at, updated_at, name, domain, system_id, path, privacy_declaration_id) "
                "VALUES (:id, :created_at, :updated_at, :name, :domain, :system_id, :path, :privacy_declaration_id)"
            ),
            id=str(uuid.uuid4()),
            created_at=row.created_at,
            updated_at=row.updated_at,
            name=row.name,
            domain=row.domain,
            system_id=row.system_id,
            privacy_declaration_id=None,
        )
=======
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
>>>>>>> 54e4eac93 (no n+1 queries)

    op.drop_column("asset", "description")
