"""Adds system managers table and client.systems

Also includes a data migration to add new scopes to fidesuserpermission.scopes and client.scopes if they
have cli-objects:-* scopes as we're making these scopes more granular.

Revision ID: 68a518a3c050
Revises: 2f6aa5fe797a
Create Date: 2023-02-23 21:52:56.225405

"""

from typing import List

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy
from sqlalchemy.sql.elements import TextClause

revision = "68a518a3c050"
down_revision = "2f6aa5fe797a"
branch_labels = None
depends_on = None

new_create_scopes = [
    "data_category:create",
    "data_qualifier:create",
    "data_subject:create",
    "data_use:create",
    "ctl_dataset:create",
    "evaluation:create",
    "organization:create",
    "ctl_policy:create",
    "registry:create",
    "system:create",
]

new_read_scopes = [
    "data_category:read",
    "data_qualifier:read",
    "data_subject:read",
    "data_use:read",
    "ctl_dataset:read",
    "evaluation:read",
    "organization:read",
    "ctl_policy:read",
    "registry:read",
    "system:read",
]

new_update_scopes = [
    "data_category:update",
    "data_qualifier:update",
    "data_subject:update",
    "data_use:update",
    "ctl_dataset:update",
    "evaluation:update",
    "organization:update",
    "ctl_policy:update",
    "registry:update",
    "system:update",
]

new_delete_scopes = [
    "data_category:delete",
    "data_qualifier:delete",
    "data_subject:delete",
    "data_use:delete",
    "ctl_dataset:delete",
    "evaluation:delete",
    "organization:delete",
    "ctl_policy:delete",
    "registry:delete",
    "system:delete",
]


def upgrade():
    op.create_table(
        "systemmanager",
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
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("system_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["system_id"], ["ctl_systems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["fidesuser.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", "user_id", "system_id"),
    )
    op.create_index(op.f("ix_systemmanager_id"), "systemmanager", ["id"], unique=False)
    op.add_column(
        "client",
        sa.Column(
            "systems", sa.ARRAY(sa.String()), server_default="{}", nullable=False
        ),
    )

    bind = op.get_bind()

    def add_new_scopes_to_fides_user_permissions(
        matched_rows: ResultProxy, new_scopes: List[str]
    ):
        """Helper method to tack on new scopes to the fidesuserpermissions.scopes if user has existing scope."""
        for row in matched_rows:
            scopes: List[str] = row["scopes"] or []
            scopes.extend(new_scopes)

            add_new_scopes_query: TextClause = text(
                "UPDATE fidesuserpermissions SET scopes= :scopes WHERE id= :id"
            )

            bind.execute(
                add_new_scopes_query,
                {"scopes": sorted(list(set(scopes))), "id": row["id"]},
            )

    def add_new_scopes_to_client(matched_rows: ResultProxy, new_scopes: List[str]):
        """Helper method to tack on new scopes to the client.scopes if user has existing scope."""
        for row in matched_rows:
            scopes: List[str] = row["scopes"] or []
            scopes.extend(new_scopes)

            add_new_scopes_query: TextClause = text(
                "UPDATE client SET scopes= :scopes WHERE id= :id"
            )

            bind.execute(
                add_new_scopes_query,
                {"scopes": sorted(list(set(scopes))), "id": row["id"]},
            )

    add_new_scopes_to_fides_user_permissions(
        matched_rows=bind.execute(
            text(
                "SELECT * FROM fidesuserpermissions WHERE 'cli-objects:create' = ANY(scopes);"
            )
        ),
        new_scopes=new_create_scopes,
    )
    add_new_scopes_to_client(
        matched_rows=bind.execute(
            text("SELECT * FROM client WHERE 'cli-objects:create' = ANY(scopes);")
        ),
        new_scopes=new_create_scopes,
    )

    add_new_scopes_to_fides_user_permissions(
        matched_rows=bind.execute(
            text(
                "SELECT * FROM fidesuserpermissions WHERE 'cli-objects:read' = ANY(scopes);"
            )
        ),
        new_scopes=new_read_scopes,
    )
    add_new_scopes_to_client(
        matched_rows=bind.execute(
            text("SELECT * FROM client WHERE 'cli-objects:read' = ANY(scopes);")
        ),
        new_scopes=new_read_scopes,
    )

    add_new_scopes_to_fides_user_permissions(
        matched_rows=bind.execute(
            text(
                "SELECT * FROM fidesuserpermissions WHERE 'cli-objects:update' = ANY(scopes);"
            )
        ),
        new_scopes=new_update_scopes,
    )

    add_new_scopes_to_client(
        matched_rows=bind.execute(
            text("SELECT * FROM client WHERE 'cli-objects:update' = ANY(scopes);")
        ),
        new_scopes=new_update_scopes,
    )

    add_new_scopes_to_fides_user_permissions(
        matched_rows=bind.execute(
            text(
                "SELECT * FROM fidesuserpermissions WHERE 'cli-objects:delete' = ANY(scopes);"
            )
        ),
        new_scopes=new_delete_scopes,
    )

    add_new_scopes_to_client(
        matched_rows=bind.execute(
            text("SELECT * FROM client WHERE 'cli-objects:delete' = ANY(scopes);")
        ),
        new_scopes=new_delete_scopes,
    )


def downgrade():
    op.drop_column("client", "systems")
    op.drop_index(op.f("ix_systemmanager_id"), table_name="systemmanager")
    op.drop_table("systemmanager")
