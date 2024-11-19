# pylint: disable=protected-access

from unittest import mock

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from fides.api.tasks import NEW_SESSION_RETRIES, DatabaseTask
from fides.config import CONFIG


class TestDatabaseTask:
    @pytest.fixture
    def mock_config_changed_db_engine_settings(self):
        pool_size = CONFIG.database.task_engine_pool_size
        CONFIG.database.task_engine_pool_size = pool_size + 5
        max_overflow = CONFIG.database.task_engine_max_overflow
        CONFIG.database.task_engine_max_overflow = max_overflow + 5
        yield
        CONFIG.database.task_engine_pool_size = pool_size
        CONFIG.database.task_engine_max_overflow = max_overflow

    @pytest.fixture
    def recovering_session_maker(self):
        """Fixture that fails twice then succeeds"""
        mock_session = mock.Mock()
        mock_maker = mock.Mock()
        mock_maker.side_effect = [
            OperationalError("connection failed", None, None),
            OperationalError("connection failed", None, None),
            mock_session,
        ]
        return mock_maker, mock_session

    @pytest.fixture
    def always_failing_session_maker(self):
        """Fixture that always fails with OperationalError"""
        mock_maker = mock.Mock()
        mock_maker.side_effect = OperationalError("connection failed", None, None)
        return mock_maker

    @pytest.mark.parametrize(
        "config_fixture", [None, "mock_config_changed_db_engine_settings"]
    )
    def test_get_task_session(self, config_fixture, request):
        if config_fixture is not None:
            request.getfixturevalue(
                config_fixture
            )  # used to invoke config fixture if provided
        pool_size = CONFIG.database.task_engine_pool_size
        max_overflow = CONFIG.database.task_engine_max_overflow
        t = DatabaseTask()
        session: Session = t.get_new_session()
        engine: Engine = session.get_bind()
        assert isinstance(engine.pool, NullPool)

    def test_retry_on_operational_error(self, recovering_session_maker):
        """Test that session creation retries on OperationalError"""

        mock_maker, mock_session = recovering_session_maker

        task = DatabaseTask()
        with mock.patch.object(task, "_sessionmaker", mock_maker):
            session = task.get_new_session()
            assert session == mock_session
            assert mock_maker.call_count == 3

    def test_max_retries_exceeded(mock_db_task, always_failing_session_maker):
        """Test that retries stop after max attempts"""
        task = DatabaseTask()
        with mock.patch.object(task, "_sessionmaker", always_failing_session_maker):
            with pytest.raises(OperationalError):
                with task.get_new_session():
                    pass
            assert always_failing_session_maker.call_count == NEW_SESSION_RETRIES
