"""Add AWS SES email provider

Revision ID: 82883b0df5e4
Revises: c961528edfc6
Create Date: 2025-02-20 14:27:58.974466

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "82883b0df5e4"
down_revision = "c961528edfc6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("alter type messagingservicetype rename to messagingservicetype_old")
    op.execute(
        "create type messagingservicetype as enum('mailchimp_transactional', 'mailgun', 'twilio_text', 'twilio_email', 'aws_ses')"
    )
    op.execute(
        (
            "alter table messagingconfig alter column service_type type messagingservicetype using "
            "service_type::text::messagingservicetype"
        )
    )
    op.execute("drop type messagingservicetype_old")


def downgrade():
    op.execute("delete from messagingconfig where service_type in ('aws_ses')")
    op.execute("alter type messagingservicetype rename to messagingservicetype_old")
    op.execute(
        "create type messagingservicetype as enum('mailchimp_transactional', 'mailgun', 'twilio_text', 'twilio_email')"
    )
    op.execute(
        (
            "alter table messagingconfig alter column service_type type messagingservicetype using "
            "service_type::text::messagingservicetype"
        )
    )
    op.execute("drop type messagingservicetype_old")
