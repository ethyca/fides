"""add html format for storageconfig

Revision ID: c1885270b3cc
Revises: 5307999c0dac
Create Date: 2023-05-31 21:43:45.404454

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c1885270b3cc"
down_revision = "5307999c0dac"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type responseformat rename to responseformat_old")
    op.execute("create type responseformat as enum('json', 'csv', 'html')")

    # drop default, change type and set default back
    op.execute("alter table storageconfig alter column format drop default")
    op.execute(
        "alter table storageconfig alter column format type responseformat using format::text::responseformat"
    )
    op.execute("alter table storageconfig alter column format set default 'json'")

    op.execute("drop type responseformat_old")


def downgrade():
    op.execute("delete from storageconfig where format = 'html'")

    op.execute("alter type responseformat rename to responseformat_old")
    op.execute("create type responseformat as enum('json', 'csv')")

    # drop default, change type and set default back
    op.execute("alter table storageconfig alter column format drop default")
    op.execute(
        "alter table storageconfig alter column format type responseformat using format::text::responseformat"
    )
    op.execute("alter table storageconfig alter column format set default 'json'")

    op.execute("drop type responseformat_old")
