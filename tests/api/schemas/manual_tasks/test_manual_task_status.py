from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionMixin,
    StatusTransitionNotAllowed,
    StatusType,
)


class TestStatusType:
    def test_valid_transitions_from_pending(self):
        transitions = StatusType.get_valid_transitions(StatusType.pending)
        assert set(transitions) == {
            StatusType.in_progress,
            StatusType.failed,
            StatusType.completed,
        }

    def test_valid_transitions_from_in_progress(self):
        transitions = StatusType.get_valid_transitions(StatusType.in_progress)
        assert set(transitions) == {StatusType.completed, StatusType.failed}

    def test_valid_transitions_from_completed(self):
        transitions = StatusType.get_valid_transitions(StatusType.completed)
        assert set(transitions) == set()

    def test_valid_transitions_from_failed(self):
        transitions = StatusType.get_valid_transitions(StatusType.failed)
        assert set(transitions) == {StatusType.pending, StatusType.in_progress}


class TestModel(StatusTransitionMixin):
    """Test implementation of StatusTransitionMixin"""

    def __init__(self):
        self.status = StatusType.pending
        self.completed_at = None
        self.completed_by_id = None


class TestStatusTransitionMixin:
    @pytest.fixture
    def model(self):
        return TestModel()

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        return db

    def test_update_status_pending_to_in_progress(self, model, mock_db):
        model.update_status(mock_db, StatusType.in_progress)
        assert model.status == StatusType.in_progress
        assert model.completed_at is None
        assert model.completed_by_id is None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_status_in_progress_to_completed(self, model, mock_db):
        model.status = StatusType.in_progress
        user_id = "test_user"
        model.update_status(mock_db, StatusType.completed, user_id)
        assert model.status == StatusType.completed
        assert isinstance(model.completed_at, datetime)
        assert model.completed_by_id == user_id

    def test_update_status_completed_to_failed(self, model, mock_db):
        model.status = StatusType.completed
        with pytest.raises(
            StatusTransitionNotAllowed, match="Invalid status transition"
        ):
            model.update_status(mock_db, StatusType.failed)

    def test_update_status_failed_to_pending(self, model, mock_db):
        model.status = StatusType.failed
        model.update_status(mock_db, StatusType.pending)
        assert model.status == StatusType.pending
        assert model.completed_at is None
        assert model.completed_by_id is None

    def test_invalid_transition_same_status(self, model, mock_db):
        with pytest.raises(StatusTransitionNotAllowed, match="already in status"):
            model.update_status(mock_db, StatusType.pending)

    def test_invalid_transition_pending_to_completed(self, model, mock_db):
        model.status = StatusType.pending
        model.update_status(mock_db, StatusType.completed)
        assert model.status == StatusType.completed
        assert isinstance(model.completed_at, datetime)
        assert model.completed_by_id is None

    def test_mark_completed(self, model, mock_db):
        model.status = StatusType.in_progress
        user_id = "test_user"
        model.mark_completed(mock_db, user_id)
        assert model.status == StatusType.completed
        assert isinstance(model.completed_at, datetime)
        assert model.completed_by_id == user_id

    def test_mark_failed(self, model, mock_db):
        model.status = StatusType.in_progress
        model.mark_failed(mock_db)
        assert model.status == StatusType.failed

    def test_start_progress(self, model, mock_db):
        model.start_progress(mock_db)
        assert model.status == StatusType.in_progress

    def test_reset_to_pending(self, model, mock_db):
        model.status = StatusType.failed
        model.reset_to_pending(mock_db)
        assert model.status == StatusType.pending
        assert model.completed_at is None
        assert model.completed_by_id is None

    def test_status_properties(self, model):
        # Test is_pending
        model.status = StatusType.pending
        assert model.is_pending
        assert not model.is_in_progress
        assert not model.is_completed
        assert not model.is_failed

        # Test is_in_progress
        model.status = StatusType.in_progress
        assert not model.is_pending
        assert model.is_in_progress
        assert not model.is_completed
        assert not model.is_failed

        # Test is_completed
        model.status = StatusType.completed
        assert not model.is_pending
        assert not model.is_in_progress
        assert model.is_completed
        assert not model.is_failed

        # Test is_failed
        model.status = StatusType.failed
        assert not model.is_pending
        assert not model.is_in_progress
        assert not model.is_completed
        assert model.is_failed
