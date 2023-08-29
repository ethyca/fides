from datetime import datetime, timedelta
from typing import Generator
from unittest import mock

import pytest
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
    def test_webhook_url_defined(self, mock_post, systems, db: Session):
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
            data={
                "modified_systems": [
                    {"fides_key": "system_a", "name": "System A"},
                    {"fides_key": "system_b", "name": "System B"},
                ]
            },
        )
