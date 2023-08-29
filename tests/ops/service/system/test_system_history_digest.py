from datetime import datetime, timedelta
from typing import Generator
from unittest import mock

import pytest
from requests import RequestException
from sqlalchemy.orm import Session

from fides.api.models.sql_models import System
from fides.api.models.system_history import SystemHistory
from fides.api.service.system.system_history_digest import send_system_change_digest
from fides.config import get_config

CONFIG = get_config()


class TestSystemHistoryDigest:
    @pytest.fixture(scope="function")
    def systems(self, db: Session) -> Generator:
        system_a = System.create(
            db=db,
            data={
                "fides_key": "system_a",
                "name": "System A",
            },
        )
        system_b = System.create(
            db=db,
            data={
                "fides_key": "system_b",
                "name": "System B",
            },
        )
        system_c = System.create(
            db=db,
            data={
                "fides_key": "system_c",
                "name": "System C",
            },
        )
        yield
        system_a.delete(db)
        system_b.delete(db)
        system_c.delete(db)

    @mock.patch("fides.api.service.system.system_history_digest.requests.post")
    def test_webhook_url_defined(self, mock_post, systems, db: Session, loguru_caplog):
        # make some system changes to verify that we deduplicate systems
        # and only return changes from within the last 24 hours
        SystemHistory(
            edited_by="fides",
            system_key="system_a",
            before={"description": ""},
            after={"description": "System A"},
        ).save(db=db)
        SystemHistory(
            edited_by="fides",
            system_key="system_a",
            before={"description": ""},
            after={"description": "System A (Prod)"},
        ).save(db=db)
        SystemHistory(
            edited_by="fides",
            system_key="system_b",
            before={"description": ""},
            after={"description": "System B"},
        ).save(db=db)
        SystemHistory(
            edited_by="fides",
            system_key="system_c",
            before={"description": ""},
            after={"description": "System C"},
            created_at=datetime.now() - timedelta(hours=48),
        ).save(db=db)

        webhook_url = "https://localhost"
        CONFIG.jobs.system_change_webhook_url = webhook_url
        send_system_change_digest.delay().get()
        mock_post.assert_called_with(
            webhook_url,
            json={
                "modified_systems": [
                    {"fides_key": "system_a", "name": "System A"},
                    {"fides_key": "system_b", "name": "System B"},
                ]
            },
        )

        assert "Starting system change digest send..." in loguru_caplog.text

        assert (
            f"Successfully posted system change digest to {webhook_url}"
            in loguru_caplog.text
        )
        assert "Found 2 modified systems." in loguru_caplog.text

    @mock.patch("fides.api.service.system.system_history_digest.requests.post")
    def test_no_modified_systems(self, mock_post, systems, db: Session):
        # No system changes are made
        send_system_change_digest.delay().get()
        mock_post.assert_not_called()

    @mock.patch("fides.api.service.system.system_history_digest.requests.post")
    def test_webhook_failure(self, mock_post, systems, db: Session, loguru_caplog):
        SystemHistory(
            edited_by="fides",
            system_key="system_a",
            before={"description": ""},
            after={"description": "System A"},
        ).save(db=db)

        # Simulate a webhook failure
        mock_post.side_effect = RequestException("Webhook error")
        send_system_change_digest.delay().get()

        assert "ERROR" in loguru_caplog.text
        assert (
            "Failed to send POST request to webhook: Webhook error"
            in loguru_caplog.text
        )

    @mock.patch("fides.api.service.system.system_history_digest.requests.post")
    @mock.patch(
        "fides.api.service.system.system_history_digest.DatabaseTask.get_new_session"
    )
    def test_database_error(
        self, mock_get_new_session, mock_post, systems, db: Session, loguru_caplog
    ):
        mock_get_new_session.side_effect = Exception("Database error")
        send_system_change_digest.delay().get()

        assert "ERROR" in loguru_caplog.text
        assert (
            "An error occurred while querying the database: Database error"
            in loguru_caplog.text
        )
