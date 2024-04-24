"""adds MAILCHIMP_TRANSACTIONAL enum

Revision ID: 39b209861471
Revises: 9f38dad37628
Create Date: 2023-03-03 21:57:14.368385

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "39b209861471"
down_revision = "9f38dad37628"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type messagingservicetype rename to messagingservicetype_old")
    op.execute(
        "create type messagingservicetype as enum('MAILCHIMP_TRANSACTIONAL', 'MAILGUN', 'TWILIO_TEXT', 'TWILIO_EMAIL')"
    )
    op.execute(
        (
            "alter table messagingconfig alter column service_type type messagingservicetype using "
            "service_type::text::messagingservicetype"
        )
    )
    op.execute("drop type messagingservicetype_old")


def downgrade():
    # return
    op.execute(
        "delete from messagingconfig where service_type in ('MAILCHIMP_TRANSACTIONAL')"
    )
    op.execute("alter type messagingservicetype rename to messagingservicetype_old")
    op.execute(
        "create type messagingservicetype as enum('MAILGUN', 'TWILIO_TEXT', 'TWILIO_EMAIL')"
    )
    op.execute(
        (
            "alter table messagingconfig alter column service_type type messagingservicetype using "
            "service_type::text::messagingservicetype"
        )
    )
    op.execute("drop type messagingservicetype_old")
