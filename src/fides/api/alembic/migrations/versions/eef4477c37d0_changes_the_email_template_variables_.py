"""Changes the email template variables syntax from {{variable_name}} to __VARIABLE_NAME__.

Revision ID: eef4477c37d0
Revises: cc37edf20859
Create Date: 2024-09-03 12:47:54.708196

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "eef4477c37d0"
down_revision = "cc37edf20859"
branch_labels = None
depends_on = None


VARIABLES = ["minutes", "days", "denial_reason", "code", "download_link"]
JSON_VARIABLES = ["subject", "body"]


def upgrade():
    for json_variable in JSON_VARIABLES:
        for variable in VARIABLES:
            statement = f"""
            UPDATE messaging_template
            SET content = jsonb_set(
                content,
                '{{{json_variable}}}',
                to_jsonb(REPLACE(content ->> '{json_variable}', '{{{{{variable}}}}}', '__{variable.upper()}__'))
            );
            """
            op.execute(statement)


def downgrade():
    for json_variable in JSON_VARIABLES:
        for variable in VARIABLES:
            statement = f"""
            UPDATE messaging_template
            SET content = jsonb_set(
                content,
                '{{{json_variable}}}',
                to_jsonb(REPLACE(content ->> '{json_variable}', '__{variable.upper()}__', '{{{{{variable}}}}}'))
            );
            """
            op.execute(statement)
