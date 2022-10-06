"""Rename user name tables and indexes

Revision ID: c7cc36820d4b
Revises: ed1b00ff963d
Create Date: 2022-06-25 15:20:20.373137

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7cc36820d4b"
down_revision = "ed1b00ff963d"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("fidesopsuser", "fidesuser")
    op.execute("ALTER INDEX fidesopsuser_pkey RENAME TO fidesuser_pkey")
    op.execute("ALTER INDEX ix_fidesopsuser_id RENAME TO ix_fidesuser_id")
    op.execute("ALTER INDEX ix_fidesopsuser_username RENAME TO ix_fidesuser_username")
    op.rename_table("fidesopsuserpermissions", "fidesuserpermissions")
    op.execute(
        "ALTER INDEX fidesopsuserpermissions_pkey RENAME TO fidesuserpermission_pkey"
    )
    op.execute(
        "ALTER INDEX fidesopsuserpermissions_user_id_key RENAME TO fidesuserpermissions_user_id_key"
    )
    op.execute(
        "ALTER INDEX ix_fidesopsuserpermissions_id RENAME TO ix_fidesuserpermissions_id"
    )
    op.drop_constraint(
        constraint_name="fidesopsuserpermissions_user_id_fkey",
        table_name="fidesuserpermissions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        constraint_name="fidesuserpermissions_user_id_fkey",
        source_table="fidesuserpermissions",
        referent_table="fidesuser",
        local_cols=["user_id"],
        remote_cols=["id"],
    )
    op.drop_constraint(
        constraint_name="client_user_id_fkey", table_name="client", type_="foreignkey"
    )
    op.create_foreign_key(
        constraint_name="client_user_id_fkey",
        source_table="client",
        referent_table="fidesuser",
        local_cols=["user_id"],
        remote_cols=["id"],
    )
    op.drop_constraint(
        constraint_name="privacyrequest_reviewed_by_fkey",
        table_name="privacyrequest",
        type_="foreignkey",
    )
    op.create_foreign_key(
        constraint_name="privacyrequest_reviewed_by_fkey",
        source_table="privacyrequest",
        referent_table="fidesuser",
        local_cols=["reviewed_by"],
        remote_cols=["id"],
    )
    op.drop_constraint(
        "privacyrequest_reviewed_by_fkey", "privacyrequest", type_="foreignkey"
    )
    op.create_foreign_key(
        None,
        "privacyrequest",
        "fidesuser",
        ["reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.rename_table("fidesuser", "fidesopsuser")
    op.execute("ALTER INDEX fidesuer_pkey RENAME TO fidesopsuser_pkey")
    op.execute("ALTER INDEX ix_fidesuer_id RENAME TO ix_fidesopsuser_id")
    op.execute("ALTER INDEX ix_fidesuer_username RENAME TO ix_fidesopsuser_username")
    op.rename_table("fidesuserpermissions", "fidesopsuserpremissions")
    op.execute(
        "ALTER INDEX fidesuerpermission_pkey RENAME TO fidesopsuserpermissions_pkey"
    )
    op.execute(
        "ALTER INDEX fidesuerpermissions_user_id_key RENAME TO fidesopsuserpermissions_user_id_key"
    )
    op.execute(
        "ALTER INDEX ix_fidesuserpermissions_id RENAME TO ix_fidesopsuserpermissions_id"
    )
    op.drop_constraint(
        constraint_name="fidesuserpermissions_user_id_fkey",
        table_name="fidesopsuserpermissions",
        type_="foreignkey",
    )
    op.create_foreign_key(
        constraint_name="fidesopsuserpermissions_user_id_fkey",
        source_table="fidesopsuserpermissions",
        referent_table="fidesopsuser",
        local_cols=["user_id"],
        remote_cols=["id"],
    )
    op.drop_constraint(
        constraint_name="client_user_id_fkey", table_name="client", type_="foreignkey"
    )
    op.create_foreign_key(
        constraint_name="client_user_id_fkey",
        source_table="client",
        referent_table="fidesopsuser",
        local_cols=["user_id"],
        remote_cols=["id"],
    )
    op.drop_constraint(
        constraint_name="privacyrequest_reviewed_by_fkey",
        table_name="privacyrequest",
        type_="foreignkey",
    )
    op.create_foreign_key(
        constraint_name="privacyrequest_reviewed_by_fkey",
        source_table="privacyrequest",
        referent_table="fidesopsuser",
        local_cols=["reviewed_by"],
        remote_cols=["id"],
    )
    op.drop_constraint(None, "privacyrequest", type_="foreignkey")
    op.create_foreign_key(
        "privacyrequest_reviewed_by_fkey",
        "privacyrequest",
        "fidesuser",
        ["reviewed_by"],
        ["id"],
    )
