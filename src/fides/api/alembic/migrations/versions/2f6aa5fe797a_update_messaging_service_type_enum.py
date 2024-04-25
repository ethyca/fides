"""update messaging service_type enum

Revision ID: 2f6aa5fe797a
Revises: d65bbc647083
Create Date: 2023-03-03 17:13:21.108111

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "2f6aa5fe797a"
down_revision = "39b209861471"
branch_labels = None
depends_on = None


def upgrade():
    # create a temp enum type for old values
    op.execute("alter type messagingservicetype rename to messagingservicetype_old")
    # create a temp column for old values
    op.alter_column(
        "messagingconfig", "service_type", new_column_name="service_type_old"
    )
    # update the temp column to use the temp enum type
    op.execute(
        (
            "alter table messagingconfig alter column service_type_old type messagingservicetype_old using "
            "service_type_old::text::messagingservicetype_old"
        )
    )

    # create the new enum type
    messagingservicetype = postgresql.ENUM(
        "mailgun",
        "twilio_text",
        "twilio_email",
        "mailchimp_transactional",
        name="messagingservicetype",
        create_type=True,
    )
    messagingservicetype.create(op.get_bind())

    # create the new column using the new enum type
    op.add_column(
        "messagingconfig",
        sa.Column(
            "service_type",
            messagingservicetype,
            nullable=True,  # allow it to be nullable temporarily
            unique=True,
        ),
    )

    # now actually migrate the old values to the new column
    session = Session(bind=op.get_bind())
    conn = session.connection()
    statement = text(
        """SELECT distinct LOWER(service_type_old::text) AS lower_service_type_old, id
FROM messagingconfig"""
    )

    result = conn.execute(statement)
    for row in result:
        op.execute(
            f"UPDATE messagingconfig SET service_type = '{row[0]}' WHERE id = '{row[1]}';"
        )

    # update our column to make it non-nullable now that it's populated
    op.alter_column("messagingconfig", "service_type", nullable=False)

    # and clean up our temporary resources
    op.drop_column("messagingconfig", "service_type_old")
    op.execute("drop type messagingservicetype_old")


def downgrade():
    # create a temp enum type for old values
    op.execute("alter type messagingservicetype rename to messagingservicetype_old")
    # create a temp column for old values
    op.alter_column(
        "messagingconfig", "service_type", new_column_name="service_type_old"
    )
    # update the temp column to use the temp enum type
    op.execute(
        (
            "alter table messagingconfig alter column service_type_old type messagingservicetype_old using "
            "service_type_old::text::messagingservicetype_old"
        )
    )

    # create the new column with the new enum type
    messagingservicetype = postgresql.ENUM(
        "MAILGUN",
        "TWILIO_TEXT",
        "TWILIO_EMAIL",
        "MAILCHIMP_TRANSACTIONAL",
        name="messagingservicetype",
        create_type=True,
    )
    messagingservicetype.create(op.get_bind())
    op.add_column(
        "messagingconfig",
        sa.Column(
            "service_type",
            messagingservicetype,
            nullable=True,  # allow it to be nullable temporarily
            unique=True,
        ),
    )

    # now actually migrate the old values to the new column
    session = Session(bind=op.get_bind())
    conn = session.connection()
    statement = text(
        """SELECT distinct UPPER(service_type_old::text) AS upper_service_type_old, id
FROM messagingconfig"""
    )

    result = conn.execute(statement)
    for row in result:
        op.execute(
            f"UPDATE messagingconfig SET service_type = '{row[0]}' WHERE id = '{row[1]}';"
        )

    # update our column to make it non-nullable now that it's populated
    op.alter_column("messagingconfig", "service_type", nullable=False)

    # and clean up our temporary resources
    op.drop_column("messagingconfig", "service_type_old")
    op.execute("drop type messagingservicetype_old")
