"""prepare storage table for html landing page

Revision ID: 5009bc20d2ba
Revises: d65bbc647083
Create Date: 2023-02-23 17:23:46.568232

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5009bc20d2ba"
down_revision = "d65bbc647083"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    downloadformat = postgresql.ENUM(
        "json",
        "csv",
        name="downloadformat",
        create_type=False,
    )
    downloadformat.create(op.get_bind())
    op.add_column(
        "storageconfig",
        sa.Column(
            "download_format",
            downloadformat,
            server_default="json",
            nullable=False,
        ),
    )
    op.add_column(
        "storageconfig",
        sa.Column(
            "html_landing_page", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.drop_column("storageconfig", "format")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "storageconfig",
        sa.Column(
            "format",
            postgresql.ENUM("json", "csv", name="responseformat"),
            server_default=sa.text("'json'::responseformat"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.drop_column("storageconfig", "html_landing_page")
    op.drop_column("storageconfig", "download_format")
    op.execute("DROP TYPE downloadformat;")
    # ### end Alembic commands ###
