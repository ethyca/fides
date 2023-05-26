"""Upgrade to fideslang 1.4

Revision ID: 63b482f5b49b
Revises: 2661f31daffb
Create Date: 2023-05-26 07:51:25.947974

"""
from alembic import op
import sqlalchemy as sa
from collections import namedtuple
from typing import List


# revision identifiers, used by Alembic.
revision = "63b482f5b49b"
down_revision = "2661f31daffb"
branch_labels = None
depends_on = None

TaxonomyUpdate = namedtuple("TaxonomyUpdate", "old new")

data_use_updates: List[TaxonomyUpdate] = [
    # Move third_party_sharing
    TaxonomyUpdate(
        "third_party_sharing.payment_processing", "essential.service.payment_processing"
    ),
    TaxonomyUpdate(
        "third_party_sharing.fraud_detection", "essential.service.fraud_detection"
    ),
    # Nest advertising under marketing
    TaxonomyUpdate("advertising.first_party", "marketing.advertising.first_party"),
    TaxonomyUpdate(
        "advertising.first_party.contextual",
        "marketing.advertising.first_party.contextual",
    ),
    TaxonomyUpdate(
        "advertising.first_party.personalized",
        "marketing.advertising.first_party.targeted",
    ),
    # Consolidate third_party uses
    TaxonomyUpdate(
        "advertising.third_party", "marketing.advertising.third_party.targeted"
    ),
    TaxonomyUpdate(
        "advertising.third_party.personalized",
        "marketing.advertising.third_party.targeted",
    ),
    TaxonomyUpdate(
        "third_party_sharing.personalized_advertising",
        "marketing.advertising.third_party.targeted",
    ),
    # Provide -> Essential
    TaxonomyUpdate("provide", "essential"),
    TaxonomyUpdate("provide.service", "essential.service"),
]


def upgrade():
    # Update every place where a data use could be
    pass


def downgrade():
    pass
