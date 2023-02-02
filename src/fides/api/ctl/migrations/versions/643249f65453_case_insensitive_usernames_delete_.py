"""case_insensitive_usernames_delete_duplicates

Revision ID: 643249f65453
Revises: 392992c7733a
Create Date: 2023-02-01 22:22:38.055862

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.types as sa_types


# revision identifiers, used by Alembic.
revision = '643249f65453'
down_revision = '392992c7733a'
branch_labels = None
depends_on = None


def upgrade():

    # Found here in the 24.2.2.4. Nondeterministic Collations section:
    # https://www.postgresql.org/docs/current/collation.html
    op.execute("CREATE COLLATION case_insensitive (provider = icu, locale = 'und-u-ks-level2', deterministic = false);")
    op.alter_column('fidesuser','username', type_=sa_types.String(collation='case_insensitive'), nullable=True)





def downgrade():
    op.alter_column('fidesuser','username', type_=sa_types.String(), nullable=True)
    op.execute("DROP COLLATION IF EXISTS case_insensitive")