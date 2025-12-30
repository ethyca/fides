"""Tests for the ConditionalDependencyBase abstract model."""

from unittest.mock import create_autospec

import pytest
from sqlalchemy.orm import Session

from fides.api.models.conditional_dependency.conditional_dependency_base import (
    ConditionalDependencyBase,
)


class TestConditionalDependencyBase:
    """Test the ConditionalDependencyBase abstract model."""

    def test_abstract_class_has_abstract_flag(self):
        """Test that the abstract base class has the SQLAlchemy abstract flag."""
        assert ConditionalDependencyBase.__abstract__ is True

    def test_get_root_condition_not_implemented(self):
        """Test that get_root_condition raises NotImplementedError in base class."""
        db = create_autospec(Session)

        with pytest.raises(
            NotImplementedError,
            match="Subclasses of ConditionalDependencyBase must implement get_root_condition",
        ):
            ConditionalDependencyBase.get_root_condition(db, test_id="test_id")

    def test_abstract_class_has_condition_tree_column(self):
        """Test that the abstract class has the condition_tree column."""
        assert "condition_tree" in ConditionalDependencyBase.__dict__
