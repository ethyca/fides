"""case_insensitive_usernames_delete_duplicates

Revision ID: 643249f65453
Revises: 392992c7733a
Create Date: 2023-02-01 22:22:38.055862

"""
from alembic import op
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import text

from fides.lib.models.fides_user import FidesUser
from fides.lib.models.fides_user_permissions import FidesUserPermissions

# revision identifiers, used by Alembic.
revision = "643249f65453"
down_revision = "392992c7733a"
branch_labels = None
depends_on = None


def upgrade():

    # Found here in the 24.2.2.4. Nondeterministic Collations section:
    # https://www.postgresql.org/docs/current/collation.html
    op.execute(
        "CREATE COLLATION IF NOT EXISTS case_insensitive (provider = icu, locale = 'und-u-ks-level2', deterministic = false);"
    )
    session = Session(bind=op.get_bind())
    conn = session.connection()
    statement = text(
        """SELECT DISTINCT ON (username) username collate case_insensitive, created_at, id
FROM fidesuser
ORDER BY username, created_at ASC"""
    )

    result = conn.execute(statement)
    original_user_ids = [row[2] for row in result]
    session.query(FidesUserPermissions).filter(
        FidesUserPermissions.user_id.not_in(original_user_ids)
    ).delete()
    session.query(FidesUser).filter(FidesUser.id.not_in(original_user_ids)).delete()

    op.execute("DROP COLLATION IF EXISTS case_insensitive")


def downgrade():
    pass
