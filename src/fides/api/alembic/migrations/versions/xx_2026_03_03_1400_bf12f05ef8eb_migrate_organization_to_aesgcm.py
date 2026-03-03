"""migrate organization encrypted columns from pgcrypto to aesgcm

Replaces PGEncryptedString (PostgreSQL pgcrypto pgp_sym_encrypt/decrypt)
with StringEncryptedType(AesGcmEngine) on the Organization model's
controller, data_protection_officer, and representative columns.

Uses expand-contract: add new Text columns, decrypt old BYTEA values with
pgp_sym_decrypt and re-encrypt with AES-GCM, then drop old columns and
rename.

Revision ID: bf12f05ef8eb
Revises: 074796d61d8a
Create Date: 2026-03-03 14:00:00.000000

"""

import json

import sqlalchemy as sa
from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.config import CONFIG

revision = "bf12f05ef8eb"
down_revision = "074796d61d8a"
branch_labels = None
depends_on = None

COLUMNS = ("controller", "data_protection_officer", "representative")


def _is_json_null(value: str) -> bool:
    """Check if a decrypted pgcrypto value represents JSON null.

    PGEncryptedString encrypted Python None as the JSON literal "null"
    via type_coerce(bindparam, JSON) + pgp_sym_encrypt. We need to detect
    this so we store true SQL NULL instead of encrypting the string "null".
    """
    try:
        return json.loads(value) is None
    except (json.JSONDecodeError, TypeError):
        return False


def upgrade() -> None:
    for col in COLUMNS:
        op.add_column(
            "ctl_organizations",
            sa.Column(f"{col}_new", sa.Text(), nullable=True),
        )

    bind = op.get_bind()

    encryptor = StringEncryptedType(
        type_in=sa.Text(),
        key=CONFIG.security.app_encryption_key,
        engine=AesGcmEngine,
        padding="pkcs5",
    )

    null_coalesce = ", ".join(
        f"CASE WHEN {c} IS NOT NULL "
        f"THEN pgp_sym_decrypt({c}, :key) "
        f"ELSE NULL END AS {c}"
        for c in COLUMNS
    )
    rows = bind.execute(
        text(f"SELECT fides_key, {null_coalesce} FROM ctl_organizations"),
        {"key": CONFIG.user.encryption_key},
    ).fetchall()

    for row in rows:
        mapping = dict(row._mapping)
        updates: dict[str, str] = {}
        for col in COLUMNS:
            plaintext = mapping[col]
            if plaintext is not None and not _is_json_null(plaintext):
                updates[f"{col}_new"] = encryptor.process_bind_param(plaintext, None)

        if updates:
            set_clause = ", ".join(f"{k} = :{k}" for k in updates)
            bind.execute(
                text(
                    f"UPDATE ctl_organizations SET {set_clause} "
                    f"WHERE fides_key = :fk"
                ),
                {"fk": mapping["fides_key"], **updates},
            )

    migrated = sum(1 for r in rows if any(dict(r._mapping)[c] for c in COLUMNS))
    logger.info("Migrated {} organization row(s) from pgcrypto to AES-GCM", migrated)

    for col in COLUMNS:
        op.drop_column("ctl_organizations", col)
        op.alter_column("ctl_organizations", f"{col}_new", new_column_name=col)


def downgrade() -> None:
    for col in COLUMNS:
        op.add_column(
            "ctl_organizations",
            sa.Column(f"{col}_old", sa.LargeBinary(), nullable=True),
        )

    bind = op.get_bind()

    decryptor = StringEncryptedType(
        type_in=sa.Text(),
        key=CONFIG.security.app_encryption_key,
        engine=AesGcmEngine,
        padding="pkcs5",
    )

    rows = bind.execute(
        text(
            "SELECT fides_key, controller, data_protection_officer, representative "
            "FROM ctl_organizations"
        )
    ).fetchall()

    for row in rows:
        mapping = dict(row._mapping)
        updates: dict[str, str] = {}
        for col in COLUMNS:
            ciphertext = mapping[col]
            if ciphertext is not None:
                plaintext = decryptor.process_result_value(ciphertext, None)
                updates[col] = plaintext

        if updates:
            set_clauses = ", ".join(
                f"{col}_old = pgp_sym_encrypt(CAST(:{col} AS text), :key)"
                for col in updates
            )
            bind.execute(
                text(
                    f"UPDATE ctl_organizations SET {set_clauses} "
                    f"WHERE fides_key = :fk"
                ),
                {
                    "fk": mapping["fides_key"],
                    "key": CONFIG.user.encryption_key,
                    **updates,
                },
            )

    for col in COLUMNS:
        op.drop_column("ctl_organizations", col)
        op.alter_column("ctl_organizations", f"{col}_old", new_column_name=col)
