"""update stagedresource chid_diff_statuses to booleans

Revision ID: 9cad5a5c438c
Revises: d9064e71f69d
Create Date: 2024-08-27 07:45:33.495919

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection

# revision identifiers, used by Alembic.
revision = "9cad5a5c438c"
down_revision = "d9064e71f69d"
branch_labels = None
depends_on = None


def upgrade():
    bind: Connection = op.get_bind()
    # upgrade query sets child_diff_statuses JSON keys to have a value of 'true' if they currently have a value > 0;
    # otherwise, the key is not added.
    # this is done for each diff status, which are the possible keys in child_diff_statuses:
    # - monitored
    # - addition
    # - removal
    # - muted
    # - classification_addition
    # - classification_update
    upgrade_query = text(
        """
update
   stagedresource
set
   child_diff_statuses = '{}' || jsonb_strip_nulls(jsonb_build_object('monitored',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'monitored') = 'number'
         and
         (
            child_diff_statuses -> 'monitored'
         )
         ::integer > 0
      then
         true
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('addition',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'addition') = 'number'
         and
         (
            child_diff_statuses -> 'addition'
         )
         ::integer > 0
      then
         true
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('removal',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'removal') = 'number'
         and
         (
            child_diff_statuses -> 'removal'
         )
         ::integer > 0
      then
         true
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('muted',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'muted') = 'number'
         and
         (
            child_diff_statuses -> 'muted'
         )
         ::integer > 0
      then
         true
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('classification_addition',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'classification_addition') = 'number'
         and
         (
            child_diff_statuses -> 'classification_addition'
         )
         ::integer > 0
      then
         true
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('classification_update',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'classification_update') = 'number'
         and
         (
            child_diff_statuses -> 'classification_update'
         )
         ::integer > 0
      then
         true
      else
         null
   end
))
"""
    )
    bind.execute(upgrade_query)


def downgrade():
    bind: Connection = op.get_bind()
    # downgrade query sets child_diff_statuses JSON keys to have a value of '1' if they currently have a value of true;
    # otherwise, the key is not added.
    # this is done for each diff status, which are the possible keys in child_diff_statuses:
    # - monitored
    # - addition
    # - removal
    # - muted
    # - classification_addition
    # - classification_update
    downgrade_query = text(
        """
update
   stagedresource
set
   child_diff_statuses = '{}' || jsonb_strip_nulls(jsonb_build_object('monitored',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'monitored') = 'boolean'
         and
         (
            child_diff_statuses -> 'monitored'
         )
         ::boolean
      then
         1
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('addition',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'addition') = 'boolean'
         and
         (
            child_diff_statuses -> 'addition'
         )
         ::boolean
      then
         1
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('removal',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'removal') = 'boolean'
         and
         (
            child_diff_statuses -> 'removal'
         )
         ::boolean
      then
         1
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('muted',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'muted') = 'boolean'
         and
         (
            child_diff_statuses -> 'muted'
         )
         ::boolean
      then
         1
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('classification_addition',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'classification_addition') = 'boolean'
         and
         (
            child_diff_statuses -> 'classification_addition'
         )
         ::boolean
      then
         1
      else
         null
   end
)) || jsonb_strip_nulls(jsonb_build_object('classification_update',
   case
      when
         jsonb_typeof(child_diff_statuses -> 'classification_update') = 'boolean'
         and
         (
            child_diff_statuses -> 'classification_update'
         )
         ::boolean
      then
         1
      else
         null
   end
))
"""
    )
    bind.execute(downgrade_query)
