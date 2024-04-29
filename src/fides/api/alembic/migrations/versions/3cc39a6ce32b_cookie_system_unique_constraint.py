"""cookie_system_unique_constraint

Revision ID: 3cc39a6ce32b
Revises: 842790fa918a
Create Date: 2023-11-07 18:07:42.861201

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = "3cc39a6ce32b"
down_revision = "842790fa918a"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # Remove duplicate cookies on system id and system name first
    bind.execute(
        text(
            "DELETE FROM cookies A USING cookies B "
            "WHERE A.id < B.id AND A.name = B.name "
            "AND A.system_id = B.system_id "
            "AND A.system_id IS NOT NULL"
        )
    )

    # Add unique cookie on name and system id
    op.create_unique_constraint(
        "_cookie_name_system_uc", "cookies", ["name", "system_id"]
    )


def downgrade():
    op.drop_constraint("_cookie_name_system_uc", "cookies", type_="unique")
