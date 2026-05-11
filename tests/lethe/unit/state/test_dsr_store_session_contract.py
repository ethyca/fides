"""Session-boundary checks for ``DSRStore`` (callers own ``commit``/``rollback``).

Location: ``tests/lethe/unit/state/``. Marker: ``@pytest.mark.unit``.
"""

from unittest.mock import MagicMock, create_autospec

import pytest
from sqlalchemy.orm import Session

from lethe.state import DSRStore

pytestmark = pytest.mark.unit


def test_write_encryption_flushes_without_commit() -> None:
    session = create_autospec(Session, instance=True)
    pr = MagicMock()
    pr.encryption_key = None
    session.get.return_value = pr

    store = DSRStore(session, "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    store.write_encryption("key", "secret", expire_seconds=3600)

    session.flush.assert_called()
    session.commit.assert_not_called()
