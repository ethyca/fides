import asyncio

import boto3
import httpx
import pytest
import requests
from fastapi.testclient import TestClient
from httpx import AsyncClient
from moto import mock_aws
from pytest import MonkeyPatch
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fides.api.db.base_class import Base
from fides.api.db.ctl_session import sync_engine
from fides.api.db.session import get_db_engine, get_db_session
from fides.api.main import app
from fides.api.schemas.storage.storage import StorageDetails
from fides.api.tasks.scheduled.scheduler import async_scheduler, scheduler
from fides.config import get_config
from tests.helpers.db import create_citext_extension

CONFIG = get_config()


@pytest.fixture
def s3_client(storage_config):
    """Creates a mock S3 client for testing."""
    with mock_aws():
        session = boto3.Session(
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
            region_name="us-east-1",
        )
        s3 = session.client("s3")
        s3.create_bucket(Bucket=storage_config.details[StorageDetails.BUCKET.value])
        yield s3


@pytest.fixture
def mock_s3_client(s3_client, monkeypatch):
    """Fixture to mock the S3 client for attachment tests"""

    def mock_get_s3_client(auth_method, storage_secrets):
        return s3_client

    monkeypatch.setattr("fides.service.storage.s3.get_s3_client", mock_get_s3_client)
    return s3_client


@pytest.fixture(scope="session")
def db(api_client, config):
    """Return a connection to the test DB"""
    # Create the test DB engine
    assert config.test_mode
    assert requests.post != api_client.post
    engine = get_db_engine(
        database_uri=config.database.sqlalchemy_test_database_uri,
    )

    create_citext_extension(engine)

    if not scheduler.running:
        scheduler.start()
    if not async_scheduler.running:
        async_scheduler.start()

    SessionLocal = get_db_session(config, engine=engine)
    the_session = SessionLocal()
    # Setup above...

    yield the_session
    # Teardown below...
    the_session.close()
    engine.dispose()


@pytest.fixture(scope="session")
def test_client():
    """Starlette test client fixture. Easier to use mocks with when testing out API calls"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def async_session():
    assert CONFIG.test_mode

    create_citext_extension(sync_engine)

    async_engine = create_async_engine(
        f"{CONFIG.database.async_database_uri}?prepared_statement_cache_size=0",
        echo=False,
    )

    session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        yield session
        session.close()
        async_engine.dispose()


# TODO: THIS IS A HACKY WORKAROUND.
# This is specific for this test: test_get_resource_with_custom_field
# this was added to account for weird error that only happens during a
# long testing session. Something causes a config/schema change with
# the DB. Giving the test a dedicated session fixes the issue and
# matches how runtime works.
# It does look like there MAY be a small bug that is unlikely to ever
# occur during runtime. What surfaced the "benign" failure is the
# `connection_configs` relationship on the `System` model. We are
# unsure of which upstream test causes the error.
# https://github.com/MagicStack/asyncpg/blob/2f20bae772d71122e64f424cc4124e2ebdd46a58/asyncpg/exceptions/_base.py#L120-L124
# <class 'asyncpg.exceptions.InvalidCachedStatementError'>: cached statement plan is invalid due to a database schema or configuration change (SQLAlchemy asyncpg dialect will now invalidate all prepared caches in response to this exception)
@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def async_session_temp(test_client):
    assert CONFIG.test_mode

    create_citext_extension(sync_engine)

    async_engine = create_async_engine(
        CONFIG.database.async_database_uri,
        echo=False,
    )

    session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_maker() as session:
        yield session
        session.close()
        async_engine.dispose()


@pytest.fixture(scope="session")
def api_client():
    """Return a client used to make API requests"""

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
async def async_api_client():
    """Return an async client used to make API requests"""
    async with AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://0.0.0.0:8080",
        follow_redirects=True,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
async def clear_db_tables(db, async_session):
    """Clear data from tables between tests.

    If relationships are not set to cascade on delete they will fail with an
    IntegrityError if there are relationships present. This function stores tables
    that fail with this error then recursively deletes until no more IntegrityErrors
    are present.
    """
    yield

    def delete_data(tables):
        redo = []
        for table in tables:
            try:
                db.execute(table.delete())
            except IntegrityError:
                redo.append(table)
            finally:
                db.commit()

        if redo:
            delete_data(redo)

    # make sure all transactions are closed before starting deletes
    db.commit()
    await async_session.commit()

    delete_data(Base.metadata.sorted_tables)


@pytest.fixture(autouse=True, scope="session")
def monkeysession():
    """
    Monkeypatch at the session level instead of the function level.
    Automatically undoes the monkeypatching when the session finishes.
    """
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="session")
def monkeypatch_requests(test_client, monkeysession) -> None:
    """
    Some places within the application, for example `fides.cli.core.api`, use the `requests`
    library to interact with the webserver. This fixture patches those `requests` calls
    so that all of those tests instead interact with the test instance.

    NOTE: This is dangerous, now that starlette's TestClient no longer accepts allow_redirects like requests
    does - so this is not a direct drop-in any longer and the methods may need to be wrapped / transmogrified.
    """

    # Flip allow_redirects from requests to follow_redirects in starlette
    def _wrap_requests_post(url, **kwargs):
        if kwargs.get("allow_redirects") is not None:
            flag_value = kwargs.pop("allow_redirects")
            kwargs["follow_redirects"] = flag_value

        return test_client.post(url, **kwargs)

    monkeysession.setattr(requests, "get", test_client.get)
    monkeysession.setattr(requests, "post", _wrap_requests_post)
    monkeysession.setattr(requests, "put", test_client.put)
    monkeysession.setattr(requests, "patch", test_client.patch)
    monkeysession.setattr(requests, "delete", test_client.delete)


@pytest.fixture
def worker_id(request) -> str:
    """Fixture to get the xdist worker ID (e.g., 'gw0', 'gw1') or 'master'."""
    if hasattr(request.config, "workerinput"):
        # In a worker process
        return request.config.workerinput["workerid"]
    else:
        # In the master process (or not using xdist)
        return "master"
