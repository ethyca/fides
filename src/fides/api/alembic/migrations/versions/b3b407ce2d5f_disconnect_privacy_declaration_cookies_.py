"""disconnect_privacy_declaration_cookies_from_system

Revision ID: b3b407ce2d5f
Revises: ddec29f24945
Create Date: 2023-11-03 18:28:36.416814

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
from sqlalchemy import text

revision = "b3b407ce2d5f"
down_revision = "ddec29f24945"
branch_labels = None
depends_on = None


def upgrade():
    # Remove FK and add new one that cascade deletes. When Privacy Declaration is deleted, let's delete the Cookie.
    # Previously, we left it pointed to the System
    op.drop_constraint(
        "cookies_privacy_declaration_id_fkey", "cookies", type_="foreignkey"
    )
    op.create_foreign_key(
        "cookies_privacy_declaration_id_fkey",
        "cookies",
        "privacydeclaration",
        ["privacy_declaration_id"],
        ["id"],
        ondelete="CASCADE",
    )

    bind = op.get_bind()
    # Update existing cookies that are pointed to both a privacy declaration and a system id to just be
    # pointed to the privacy declaration id
    bind.execute(
        text(
            "UPDATE cookies SET system_id = null WHERE privacy_declaration_id IS NOT NULL and system_id IS NOT NULL;"
        )
    )


def downgrade():
    op.drop_constraint(
        "cookies_privacy_declaration_id_fkey", "cookies", type_="foreignkey"
    )
    op.create_foreign_key(
        "cookies_privacy_declaration_id_fkey",
        "cookies",
        "privacydeclaration",
        ["privacy_declaration_id"],
        ["id"],
        ondelete="SET NULL",
    )
