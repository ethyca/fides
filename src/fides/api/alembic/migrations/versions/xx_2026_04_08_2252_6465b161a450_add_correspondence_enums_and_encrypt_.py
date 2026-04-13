"""add_correspondence_enums_and_encrypt_comment_text

Revision ID: 6465b161a450
Revises: 1724da7ee981
Create Date: 2026-04-08 22:52:01.736340

Encrypts existing comment_text rows and seeds RBAC permissions for
correspondence scopes.

Note: CommentType and CorrespondenceDeliveryStatus are Python-only enums
stored as varchar columns — no PostgreSQL enum types are created.

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
down_revision = "1724da7ee981"
branch_labels = None
depends_on = None

CORRESPONDENCE_SCOPES = {
    "correspondence:send": "Send correspondence messages to data subjects",
    "correspondence:read": "View correspondence messages",
}

NOTIFICATION_SCOPES = {
    "notification:read": "View notifications",
}

ALL_NEW_SCOPES = {**CORRESPONDENCE_SCOPES, **NOTIFICATION_SCOPES}


def _is_encrypted(enc, value, dialect):
    """Return True if value is already AES-GCM ciphertext."""
    if value is None:
        return False
    try:
        enc.process_result_value(value, dialect)
        return True
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()

    # 1. Batch-encrypt existing comment_text rows
    # Idempotency: trial-decrypt skips rows that are already encrypted.
    # Under normal Alembic operation the transaction guarantees all-or-nothing,
    # but the guard protects against manual version-stamp edits or future
    # refactors that add per-batch commits.
    from fides.api.db.encryption_utils import encrypted_type

    enc = encrypted_type(type_in=String())

    batch_size = 500
    offset = 0
    total_encrypted = 0
    total_skipped = 0
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
            if row.comment_text is None or _is_encrypted(
                enc, row.comment_text, bind.dialect
            ):
                total_skipped += 1
                continue
            encrypted = enc.process_bind_param(row.comment_text, bind.dialect)
            bind.execute(
                text("UPDATE comment SET comment_text = :val WHERE id = :id"),
                {"val": encrypted, "id": row.id},
            )
        total_encrypted += len(rows) - total_skipped
        offset += batch_size
    if total_encrypted:
        logger.info("Encrypted {} existing comment_text rows", total_encrypted)
    if total_skipped:
        logger.info(
            "Skipped {} already-encrypted or NULL comment_text rows", total_skipped
        )

    # 2. Seed RBAC permissions for new scopes
    for scope_code, description in ALL_NEW_SCOPES.items():
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
        for scope_code in ALL_NEW_SCOPES:
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

    # 1. Remove RBAC permissions for new scopes
    for scope_code in ALL_NEW_SCOPES:
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

    # 2. Decrypt comment_text rows back to plaintext (reverse encryption)
    # Idempotency: skip rows that are already plaintext (can't be decrypted).
    from fides.api.db.encryption_utils import encrypted_type

    enc = encrypted_type(type_in=String())

    batch_size = 500
    offset = 0
    total_decrypted = 0
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
            if row.comment_text is None:
                continue
            try:
                decrypted = enc.process_result_value(row.comment_text, bind.dialect)
            except Exception:
                continue  # Already plaintext, skip
            bind.execute(
                text("UPDATE comment SET comment_text = :val WHERE id = :id"),
                {"val": decrypted, "id": row.id},
            )
            total_decrypted += 1
        offset += batch_size
    if total_decrypted:
        logger.info("Decrypted {} comment_text rows back to plaintext", total_decrypted)
