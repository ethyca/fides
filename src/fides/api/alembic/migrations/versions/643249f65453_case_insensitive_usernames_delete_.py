"""case_insensitive_usernames_delete_duplicates

Revision ID: 643249f65453
Revises: 5d62bab40b71
Create Date: 2023-02-01 22:22:38.055862

"""

from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "643249f65453"
down_revision = "5d62bab40b71"
branch_labels = None
depends_on = None


def upgrade():
    session = Session(bind=op.get_bind())
    conn = session.connection()
    statement = text(
        """SELECT DISTINCT ON (LOWER(username)) username, created_at, id
FROM fidesuser
ORDER BY LOWER(username), created_at ASC"""
    )

    result = conn.execute(statement)
    original_user_ids = [row[2] for row in result]
    op.execute(
        f"UPDATE client SET user_id = NULL WHERE NOT(user_id=ANY(ARRAY[{original_user_ids}]::varchar[]))"
    )
    op.execute(
        f"UPDATE auditlog SET user_id = 'user_deleted' WHERE NOT(user_id=ANY(ARRAY[{original_user_ids}]::varchar[]))"
    )
    op.execute(
        f"""DELETE FROM fidesuserpermissions
    WHERE NOT(user_id=ANY(ARRAY[{original_user_ids}]::varchar[]))"""
    )

    op.execute(
        f"""DELETE FROM fidesuser 
    WHERE NOT(id=ANY(ARRAY[{original_user_ids}]::varchar[]))"""
    )

    op.execute("CREATE EXTENSION IF NOT EXISTS citext;")
    op.execute("ALTER TABLE fidesuser ALTER COLUMN username TYPE citext;")


def downgrade():
    op.execute("ALTER TABLE fidesuser ALTER COLUMN username TYPE varchar;")
    op.execute("DROP EXTENSION IF EXISTS citext;")
