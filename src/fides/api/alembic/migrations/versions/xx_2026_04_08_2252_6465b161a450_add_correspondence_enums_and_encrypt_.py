"""encrypt_comment_text

Revision ID: 6465b161a450
Revises: 4738e3e3e850
Create Date: 2026-04-08 22:52:01.736340

Batch-encrypts existing comment_text rows using AES-GCM via StringEncryptedType.

PREREQ: FIDES__SECURITY__APP_ENCRYPTION_KEY must be set at migration time.
Without it, encryption will fail. Ensure this is configured in CI and fresh
environments before running migrations.
"""

from alembic import op
from loguru import logger
from sqlalchemy import String, text

from fides.api.db.encryption_utils import encrypted_type, get_encryption_key

# revision identifiers, used by Alembic.
revision = "6465b161a450"
down_revision = "4738e3e3e850"
branch_labels = None
depends_on = None


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

    # Batch-encrypt existing comment_text rows.
    # Idempotency: trial-decrypt skips rows that are already encrypted.
    # Under normal Alembic operation the transaction guarantees all-or-nothing,
    # but the guard protects against manual version-stamp edits or future
    # refactors that add per-batch commits.
    key = get_encryption_key()
    if not key:
        raise RuntimeError(
            "FIDES__SECURITY__APP_ENCRYPTION_KEY must be set to run this migration. "
            "Refusing to proceed — encrypting with an empty key would corrupt data."
        )

    enc = encrypted_type(type_in=String())

    batch_size = 500
    offset = 0
    total_encrypted = 0
    total_skipped = 0
    while True:
        # LIMIT/OFFSET is safe here because ORDER BY id is stable across UPDATEs
        # (we only modify comment_text, never id).
        rows = bind.execute(
            text(
                "SELECT id, comment_text FROM comment "
                "ORDER BY id LIMIT :limit OFFSET :offset"
            ),
            {"limit": batch_size, "offset": offset},
        ).fetchall()
        if not rows:
            break
        batch_skipped = 0
        for row in rows:
            if row.comment_text is None or _is_encrypted(
                enc, row.comment_text, bind.dialect
            ):
                batch_skipped += 1
                continue
            encrypted = enc.process_bind_param(row.comment_text, bind.dialect)
            bind.execute(
                text("UPDATE comment SET comment_text = :val WHERE id = :id"),
                {"val": encrypted, "id": row.id},
            )
        total_encrypted += len(rows) - batch_skipped
        total_skipped += batch_skipped
        offset += batch_size
    if total_encrypted:
        logger.info("Encrypted {} existing comment_text rows", total_encrypted)
    if total_skipped:
        logger.info(
            "Skipped {} already-encrypted or NULL comment_text rows", total_skipped
        )


def downgrade():
    bind = op.get_bind()

    # Decrypt comment_text rows back to plaintext (reverse encryption).
    # Idempotency: skip rows that are already plaintext (can't be decrypted).
    key = get_encryption_key()
    if not key:
        raise RuntimeError(
            "FIDES__SECURITY__APP_ENCRYPTION_KEY must be set to run this migration downgrade. "
            "Refusing to proceed — decrypting with an empty key would corrupt data."
        )

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
    else:
        non_null = bind.execute(
            text("SELECT count(*) FROM comment WHERE comment_text IS NOT NULL")
        ).scalar()
        if non_null:
            logger.warning(
                "Downgrade decrypted 0 of {} non-null comment_text rows. "
                "Verify FIDES__SECURITY__APP_ENCRYPTION_KEY matches the key "
                "used during the upgrade.",
                non_null,
            )
