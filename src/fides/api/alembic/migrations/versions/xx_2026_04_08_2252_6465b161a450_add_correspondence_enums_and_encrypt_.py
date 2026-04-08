"""add_correspondence_enums_and_encrypt_comment_text

Revision ID: 6465b161a450
Revises: 6a42f48c23dd
Create Date: 2026-04-08 22:52:01.736340

Creates the correspondencedeliverystatus PostgreSQL enum (for use by the
CorrespondenceMetadata table in a follow-up migration), encrypts existing
comment_text rows, and seeds RBAC permissions for correspondence scopes.

Note: CommentType new values (message_to_subject, reply_from_subject) do NOT
require a DB migration because the comment_type column is varchar, not a
PostgreSQL enum. Validation happens at the SQLAlchemy model layer.

PREREQ: FIDES__SECURITY__APP_ENCRYPTION_KEY must be set at migration time.
Without it, encryption will fail. Ensure this is configured in CI and fresh
environments before running migrations.
"""

from uuid import uuid4

from alembic import op
from loguru import logger
from sqlalchemy import String, text

# revision identifiers, used by Alembic.
revision = "6465b161a450"
down_revision = "6a42f48c23dd"
branch_labels = None
depends_on = None

CORRESPONDENCE_SCOPES = {
    "correspondence:send": "Send correspondence messages to data subjects",
    "correspondence:read": "View correspondence messages",
    "notification:read": "View notifications",
}


def upgrade():
    # 1. Create correspondencedeliverystatus enum (used by PR 2's metadata table)
    bind = op.get_bind()
    type_exists = bind.execute(
        text("SELECT 1 FROM pg_type WHERE typname = 'correspondencedeliverystatus'")
    ).fetchone()
    if not type_exists:
        op.execute(
            "CREATE TYPE correspondencedeliverystatus AS ENUM "
            "('pending', 'sent', 'delivered', 'bounced', 'failed')"
        )

    # 2. Batch-encrypt existing comment_text rows
    from fides.api.db.encryption_utils import encrypted_type

    enc = encrypted_type(type_in=String())

    batch_size = 500
    offset = 0
    total_encrypted = 0
    while True:
        rows = bind.execute(
            text(
                "SELECT id, comment_text FROM comment "
                "ORDER BY id LIMIT :limit OFFSET :offset"
            ),
            {"limit": batch_size, "offset": offset},
        ).fetchall()
        if not rows:
            break
        for row in rows:
            encrypted = enc.process_bind_param(row.comment_text, bind.dialect)
            bind.execute(
                text("UPDATE comment SET comment_text = :val WHERE id = :id"),
                {"val": encrypted, "id": row.id},
            )
        total_encrypted += len(rows)
        offset += batch_size
    if total_encrypted:
        logger.info("Encrypted {} existing comment_text rows", total_encrypted)

    # 3. Seed RBAC permissions for correspondence scopes
    for scope_code, description in CORRESPONDENCE_SCOPES.items():
        resource_type = scope_code.split(":")[0]
        bind.execute(
            text(
                "INSERT INTO rbac_permission (id, code, description, resource_type, is_active, created_at, updated_at) "
                "VALUES (:id, :code, :description, :resource_type, true, now(), now()) "
                "ON CONFLICT (code) DO NOTHING"
            ),
            {
                "id": str(uuid4()),
                "code": scope_code,
                "description": description,
                "resource_type": resource_type,
            },
        )

    # Assign new scopes to the owner role
    owner_role = bind.execute(
        text("SELECT id FROM rbac_role WHERE key = 'owner'")
    ).fetchone()
    if owner_role:
        for scope_code in CORRESPONDENCE_SCOPES:
            permission = bind.execute(
                text("SELECT id FROM rbac_permission WHERE code = :code"),
                {"code": scope_code},
            ).fetchone()
            if permission:
                bind.execute(
                    text(
                        "INSERT INTO rbac_role_permission (role_id, permission_id, created_at) "
                        "VALUES (:role_id, :permission_id, now()) "
                        "ON CONFLICT DO NOTHING"
                    ),
                    {
                        "role_id": owner_role.id,
                        "permission_id": permission.id,
                    },
                )


def downgrade():
    bind = op.get_bind()

    # 1. Remove RBAC permissions for correspondence scopes
    for scope_code in CORRESPONDENCE_SCOPES:
        permission = bind.execute(
            text("SELECT id FROM rbac_permission WHERE code = :code"),
            {"code": scope_code},
        ).fetchone()
        if permission:
            bind.execute(
                text("DELETE FROM rbac_role_permission WHERE permission_id = :pid"),
                {"pid": permission.id},
            )
            bind.execute(
                text("DELETE FROM rbac_permission WHERE id = :id"),
                {"id": permission.id},
            )

    # 2. Decrypt comment_text rows back to plaintext
    from fides.api.db.encryption_utils import encrypted_type

    enc = encrypted_type(type_in=String())

    batch_size = 500
    offset = 0
    while True:
        rows = bind.execute(
            text(
                "SELECT id, comment_text FROM comment "
                "ORDER BY id LIMIT :limit OFFSET :offset"
            ),
            {"limit": batch_size, "offset": offset},
        ).fetchall()
        if not rows:
            break
        for row in rows:
            decrypted = enc.process_result_value(row.comment_text, bind.dialect)
            bind.execute(
                text("UPDATE comment SET comment_text = :val WHERE id = :id"),
                {"val": decrypted, "id": row.id},
            )
        offset += batch_size

    # 3. Drop correspondencedeliverystatus enum
    op.execute("DROP TYPE IF EXISTS correspondencedeliverystatus")
