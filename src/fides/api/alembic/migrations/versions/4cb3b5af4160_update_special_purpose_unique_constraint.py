"""update_special_purpose_unique_constraint

Revision ID: 4cb3b5af4160
Revises: 8c54e1e5bdc4
Create Date: 2023-09-27 22:58:43.064996

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4cb3b5af4160"
down_revision = "8c54e1e5bdc4"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "identity_special_purpose", "currentprivacypreference", type_="unique"
    )
    op.create_unique_constraint(
        "identity_special_purpose",
        "currentprivacypreference",
        ["provided_identity_id", "special_purpose"],
    )


def downgrade():
    op.drop_constraint(
        "identity_special_purpose", "currentprivacypreference", type_="unique"
    )
    op.create_unique_constraint(
        "identity_special_purpose",
        "currentprivacypreference",
        ["provided_identity_id", "purpose"],
    )
