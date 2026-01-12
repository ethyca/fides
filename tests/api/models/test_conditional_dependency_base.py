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

    def test_get_condition_tree_not_implemented(self):
        """Test that get_condition_tree raises NotImplementedError in base class."""
        db = create_autospec(Session)

        with pytest.raises(
            NotImplementedError,
            match="Subclasses of ConditionalDependencyBase must implement get_condition_tree",
        ):
            ConditionalDependencyBase.get_condition_tree(db, test_id="test_id")

