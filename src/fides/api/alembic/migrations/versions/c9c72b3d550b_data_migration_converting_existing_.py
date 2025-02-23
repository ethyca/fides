"""data migration converting existing 'Cookies' resources to 'Asset' resources with type 'Cookie'

Revision ID: c9c72b3d550b
Revises: c961528edfc6
Create Date: 2025-02-18 18:33:56.039924

"""

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
            "SELECT id, created_at, updated_at, name, domain, system_id, path, privacy_declaration_id FROM cookies"
        )
    )

    for row in result:
        data_use_result = connection.execute(
            sa.text(
                "SELECT data_use FROM privacydeclaration WHERE id = :privacy_declaration_id"
            ),
            privacy_declaration_id=row.privacy_declaration_id,
        ).fetchone()

        data_uses = [data_use_result.data_use] if data_use_result else []

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

    op.drop_column("asset", "description")
