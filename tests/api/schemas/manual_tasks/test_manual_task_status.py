from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from fides.api.schemas.manual_tasks.manual_task_status import (
    StatusTransitionMixin,
    StatusTransitionNotAllowed,
    StatusTransitionProtocol,
    StatusType,
    validate_status_transition_object,
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


class TestStatusTransitionProtocol:
    """Test the StatusTransitionProtocol interface and validation."""

    def test_protocol_interface_definition(self):
        """Test that the Protocol defines the correct interface."""
        # Verify the Protocol has all required attributes
        assert hasattr(StatusTransitionProtocol, "__annotations__")
        annotations = StatusTransitionProtocol.__annotations__

        # Check required attributes
        assert "status" in annotations
        assert "completed_at" in annotations
        assert "completed_by_id" in annotations

        # Check that the Protocol has method signatures
        assert hasattr(StatusTransitionProtocol, "update_status")
        assert hasattr(StatusTransitionProtocol, "mark_completed")
        assert hasattr(StatusTransitionProtocol, "mark_failed")
        assert hasattr(StatusTransitionProtocol, "start_progress")
        assert hasattr(StatusTransitionProtocol, "reset_to_pending")

    def test_validate_status_transition_object_with_valid_object(self):
        """Test validation with a properly implemented object."""

        class ValidStatusObject:
            def __init__(self):
                self.status = StatusType.pending
                self.completed_at = None
                self.completed_by_id = None

            def update_status(self, db, new_status, user_id=None):
                pass

            def mark_completed(self, db, user_id):
                pass

            def mark_failed(self, db):
                pass

            def start_progress(self, db):
                pass

            def reset_to_pending(self, db):
                pass

            @property
            def is_completed(self):
                return self.status == StatusType.completed

            @property
            def is_failed(self):
                return self.status == StatusType.failed

            @property
            def is_in_progress(self):
                return self.status == StatusType.in_progress

            @property
            def is_pending(self):
                return self.status == StatusType.pending

        valid_obj = ValidStatusObject()
        assert validate_status_transition_object(valid_obj) is True

    def test_validate_status_transition_object_with_invalid_object(self):
        """Test validation with an object missing required attributes/methods."""

        class InvalidStatusObject:
            def __init__(self):
                # Missing required attributes
                pass

        invalid_obj = InvalidStatusObject()
        assert validate_status_transition_object(invalid_obj) is False

    def test_validate_status_transition_object_with_partial_implementation(self):
        """Test validation with an object that has some but not all required elements."""

        class PartialStatusObject:
            def __init__(self):
                self.status = StatusType.pending
                # Missing completed_at and completed_by_id
                pass

        partial_obj = PartialStatusObject()
        assert validate_status_transition_object(partial_obj) is False

    def test_protocol_structural_typing(self):
        """Test that objects can be used as the Protocol type without explicit inheritance."""

        class StructuralStatusObject:
            def __init__(self):
                self.status = StatusType.pending
                self.completed_at = None
                self.completed_by_id = None

            def update_status(self, db, new_status, user_id=None):
                pass

            def mark_completed(self, db, user_id):
                pass

            def mark_failed(self, db):
                pass

            def start_progress(self, db):
                pass

            def reset_to_pending(self, db):
                pass

            @property
            def is_completed(self):
                return self.status == StatusType.completed

            @property
            def is_failed(self):
                return self.status == StatusType.failed

            @property
            def is_in_progress(self):
                return self.status == StatusType.in_progress

            @property
            def is_pending(self):
                return self.status == StatusType.pending

        # This should work due to structural typing
        protocol_obj: StatusTransitionProtocol = StructuralStatusObject()
        assert validate_status_transition_object(protocol_obj) is True


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

    def test_mixin_implements_protocol(self, model):
        """Test that the mixin properly implements the StatusTransitionProtocol."""
        # Verify the mixin can be used as the protocol type
        protocol_obj: StatusTransitionProtocol = model
        assert validate_status_transition_object(protocol_obj) is True

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

    def test_transition_pending_to_completed(self, model, mock_db):
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
