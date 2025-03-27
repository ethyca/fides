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
from fides.api.util.data_category import get_data_categories_from_db
from tests.conftest import create_citext_extension


@pytest.fixture(scope="session", autouse=True)
def setup_db(api_client, config):
    """Apply migrations at beginning and end of testing session"""
    assert config.test_mode
    assert requests.post != api_client.post
    yield api_client.post(url=f"{config.cli.server_url}/v1/admin/db/reset")


@pytest.fixture(autouse=True)
def clear_db_tables(db):
    """Clear data from tables between tests.

    If relationships are not set to cascade on delete they will fail with an
    IntegrityError if there are relationsips present. This function stores tables
    that fail with this error then recursively deletes until no more IntegrityErrors
    are present.
    """
    yield

    SKIP_TABLES = ["ctl_data_categories"]

    def delete_data(tables):
        redo = []
        for table in tables:
            if table.name in SKIP_TABLES:
                # Don't purge _all_ tables
                continue

            try:
                db.execute(table.delete())
            except IntegrityError:
                redo.append(table)
            finally:
                db.commit()

        if redo:
            delete_data(redo)

    db.commit()  # make sure all transactions are closed before starting deletes
    delete_data(Base.metadata.sorted_tables)


@pytest.fixture(scope="session", autouse=True)
def fideslang_data_categories(db):
    """
    Creates a database record for each data category in the fideslang taxonomy.
    """

    categories = []
    existing_categories = get_data_categories_from_db(db)

    for default_category in DEFAULT_TAXONOMY.data_category:
        if default_category.fides_key not in existing_categories:
            try:
                categories.append(
                    DataCategoryDbModel.from_fideslang_obj(default_category).save(db)
                )
            except IntegrityError:
                pass

    yield categories

    for category in categories:
        try:
            category.delete(db)
        except ObjectDeletedError:
            pass
