"""Redo roles scopes mapping

Revision ID: 9f38dad37628
Revises: eb1e6ec39b83
Create Date: 2023-03-03 16:53:03.553992

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy

revision = "9f38dad37628"
down_revision = "eb1e6ec39b83"
branch_labels = None
depends_on = None


def swap_roles(old_role: str, new_role: str):
    bind = op.get_bind()
    matched_rows: ResultProxy = bind.execute(
        text("SELECT * FROM fidesuserpermissions WHERE :old_role = ANY(roles);"),
        {"old_role": old_role},
    )
    for row in matched_rows:
        current_roles = row["roles"]
        current_roles.remove(old_role)
        current_roles.append(new_role)
        bind.execute(
            text("UPDATE fidesuserpermissions SET roles= :roles WHERE id= :id"),
            {"roles": sorted(list(set(current_roles))), "id": row["id"]},
        )

    matched_client_rows: ResultProxy = bind.execute(
        text("SELECT * FROM client WHERE :old_role = ANY(roles);"),
        {"old_role": old_role},
    )
    for row in matched_client_rows:
        client_roles = row["roles"]
        client_roles.remove(old_role)
        client_roles.append(new_role)
        bind.execute(
            text("UPDATE client SET roles= :roles WHERE id= :id"),
            {"roles": sorted(list(set(client_roles))), "id": row["id"]},
        )


def upgrade():
    swap_roles("admin", "owner")
    swap_roles("viewer_and_privacy_request_manager", "viewer_and_approver")
    swap_roles("privacy_request_manager", "approver")


def downgrade():
    swap_roles("owner", "admin")
    swap_roles("viewer_and_approver", "viewer_and_privacy_request_manager")
    swap_roles("approver", "privacy_request_manager")
