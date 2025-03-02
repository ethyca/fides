"""This file is only for the database fixture. For all other fixtures add them to the
tests/conftest.py file.
"""

import pytest
import requests
from fideslang import DEFAULT_TAXONOMY
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import ObjectDeletedError

from fides.api.db.base import Base
from fides.api.db.session import get_db_engine, get_db_session
from fides.api.models.sql_models import DataCategory as DataCategoryDbModel
from fides.api.tasks.scheduled.scheduler import async_scheduler, scheduler
from tests.fixtures.db_fixtures import db, fideslang_data_categories, reset_db_after_test

# Note: We're importing the standardized fixtures directly from db_fixtures.py
# Both the db and reset_db_after_test fixtures will handle database setup and cleaning

# The following fixtures are no longer needed as they are replaced by the standardized versions:
# - setup_db (handled by db fixture)
# - clear_db_tables (handled by reset_db_after_test)
# - fideslang_data_categories (now directly imported from db_fixtures.py)
