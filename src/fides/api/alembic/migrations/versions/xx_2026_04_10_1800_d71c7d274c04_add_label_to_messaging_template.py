"""Add label column to messaging_template

Revision ID: d71c7d274c04
Revises: b3c8d5e7f2a1
Create Date: 2026-04-10 18:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "d71c7d274c04"
down_revision = "b3c8d5e7f2a1"
branch_labels = None
depends_on = None

# Maps MessagingActionType values to their default labels.
# Must stay in sync with DEFAULT_MESSAGING_TEMPLATES in messaging_template.py.
DEFAULT_LABELS = {
    "subject_identity_verification": "Subject identity verification",
    "privacy_request_receipt": "Privacy request received",
    "privacy_request_review_approve": "Privacy request approved",
    "privacy_request_review_deny": "Privacy request denied",
    "privacy_request_complete_access": "Access request completed",
    "privacy_request_complete_deletion": "Erasure request completed",
    "privacy_request_complete_consent": "Consent request completed",
    "manual_task_digest": "Manual task digest",
    "external_user_welcome": "External user welcome",
}


def upgrade():
    # Phase 1: Add nullable column
    op.add_column(
        "messaging_template",
        sa.Column("label", sa.String(), nullable=True),
    )

    # Phase 2: Backfill labels
    conn = op.get_bind()

    # Backfill from known defaults
    for template_type, label in DEFAULT_LABELS.items():
        conn.execute(
            sa.text(
                "UPDATE messaging_template SET label = :label "
                "WHERE type = :type AND label IS NULL"
            ),
            {"label": label, "type": template_type},
        )

    # Backfill any remaining rows (types not in DEFAULT_LABELS) with title-cased type
    conn.execute(
        sa.text(
            "UPDATE messaging_template SET label = INITCAP(REPLACE(type, '_', ' ')) "
            "WHERE label IS NULL"
        )
    )

    # Deduplicate: if multiple rows share (type, label), append a suffix
    dupes = conn.execute(
        sa.text(
            "SELECT type, label FROM messaging_template "
            "GROUP BY type, label HAVING COUNT(*) > 1"
        )
    ).fetchall()

    for template_type, label in dupes:
        rows = conn.execute(
            sa.text(
                "SELECT id FROM messaging_template "
                "WHERE type = :type AND label = :label "
                "ORDER BY updated_at DESC"
            ),
            {"type": template_type, "label": label},
        ).fetchall()
        # Keep the first (most recently updated) as-is, suffix the rest
        for i, row in enumerate(rows[1:], start=2):
            conn.execute(
                sa.text(
                    "UPDATE messaging_template SET label = :new_label WHERE id = :id"
                ),
                {"new_label": f"{label} ({i})", "id": row[0]},
            )

    # Phase 3: Set NOT NULL and add unique constraint
    op.alter_column("messaging_template", "label", nullable=False)
    op.create_unique_constraint(
        "uq_messaging_template_type_label",
        "messaging_template",
        ["type", "label"],
    )


def downgrade():
    op.drop_constraint(
        "uq_messaging_template_type_label",
        "messaging_template",
        type_="unique",
    )
    op.drop_column("messaging_template", "label")
