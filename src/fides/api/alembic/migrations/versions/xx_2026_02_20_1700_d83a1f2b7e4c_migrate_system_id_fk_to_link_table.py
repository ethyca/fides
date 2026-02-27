"""migrate system_id FK data to system_connection_config_link and drop column

Revision ID: d83a1f2b7e4c
Revises: 454edc298288
Create Date: 2026-02-20 17:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "d83a1f2b7e4c"
down_revision = "454edc298288"
branch_labels = None
depends_on = None


def upgrade():
    # Copy existing system_id values from connectionconfig into the link table
    op.execute(
        """
        INSERT INTO system_connection_config_link
            (id, system_id, connection_config_id, created_at, updated_at)
        SELECT
            'sys_' || gen_random_uuid()::text,
            system_id,
            id,
            COALESCE(created_at, now()),
            now()
        FROM connectionconfig
        WHERE system_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM system_connection_config_link scl
            WHERE scl.system_id = connectionconfig.system_id
            AND scl.connection_config_id = connectionconfig.id
        )
        """
    )

    # Drop the old FK, index, and column
    op.drop_constraint(
        "connectionconfig_system_id_fkey", "connectionconfig", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_connectionconfig_system_id"), table_name="connectionconfig"
    )
    op.drop_column("connectionconfig", "system_id")


def downgrade():
    # Re-add the system_id column
    op.add_column(
        "connectionconfig",
        sa.Column("system_id", sa.String(), nullable=True),
    )
    op.create_index(
        op.f("ix_connectionconfig_system_id"),
        "connectionconfig",
        ["system_id"],
    )
    op.create_foreign_key(
        "connectionconfig_system_id_fkey",
        "connectionconfig",
        "ctl_systems",
        ["system_id"],
        ["id"],
    )

    # Populate system_id from the link table (take the first linked system)
    op.execute(
        """
        UPDATE connectionconfig
        SET system_id = subq.system_id
        FROM (
            SELECT DISTINCT ON (connection_config_id)
                connection_config_id, system_id
            FROM system_connection_config_link
            ORDER BY connection_config_id, created_at ASC
        ) subq
        WHERE connectionconfig.id = subq.connection_config_id
        """
    )
