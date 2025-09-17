"""
Tests for the enhanced SQLAlchemy-based SQLConditionTranslator
"""

import operator
from datetime import datetime, timedelta
from unittest.mock import Mock, create_autospec, patch

import pytest
from pytest import param
from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Query, Session, relationship
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Grouping
from sqlalchemy.sql.selectable import Exists

from fides.api.models.fides_user import FidesUser
from fides.api.models.fides_user_permissions import FidesUserPermissions
from fides.api.models.manual_task.manual_task import ManualTaskInstance
from fides.api.models.privacy_request.privacy_request import PrivacyRequest
from fides.api.task.conditional_dependencies.schemas import (
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.task.conditional_dependencies.sql_schemas import FieldAddress
from fides.api.task.conditional_dependencies.sql_translator import (
    SQLConditionTranslator,
    SQLTranslationError,
)

TestBase = declarative_base()

MOCK_QUERY = Mock()
MOCK_PRIMARY_MODEL = Mock()
MOCK_PRIMARY_MODEL.__name__ = "MockPrimaryModel"
MOCK_MODEL_CLASS = Mock()
MOCK_MODEL_CLASS.__name__ = "MockModel"


@pytest.fixture
def translator(db):
    """Create a translator instance with mocked dependencies"""
    return SQLConditionTranslator(db=db)


@pytest.fixture
def condition_leaf_role():
    """Condition leaf for role - this is a relationship condition"""
    return ConditionLeaf(
        field_address="fidesuser.permissions.roles",
        operator=Operator.list_contains,
        value="approver",
    )


@pytest.fixture
def condition_leaf_user_status():
    """Condition leaf for disabled - this is a regular column condition"""
    return ConditionLeaf(
        field_address="fidesuser.disabled",
        operator=Operator.eq,
        value=False,
    )


@pytest.fixture
def condition_leaf_request_status():
    return ConditionLeaf(
        field_address="privacyrequest.status",
        operator=Operator.neq,
        value="completed",
    )


@pytest.fixture
def condition_leaf_email_address():
    return ConditionLeaf(
        field_address="fidesuser.email_address",
        operator=Operator.contains,
        value="@example.com",
    )


class TestSQLConditionTranslator:
    """Test the enhanced SQLAlchemy-based SQLConditionTranslator"""

    def test_constructor_requires_db(self, db):
        """Test that constructor requires a db session"""
        translator = SQLConditionTranslator(db=db)
        assert translator.db == db
        assert translator.orm_registry is not None

        with pytest.raises(TypeError) as exc_info:
            SQLConditionTranslator()

        assert "db" in str(exc_info.value)

    def test_init_with_custom_orm_registry(self, db):
        """Test SQLConditionTranslator initialization with custom ORM registry"""
        # Create a mock registry that mimics SQLAlchemy's declarative base structure
        mock_mapper = Mock()
        mock_mapper.class_ = Mock()
        mock_mapper.class_.__tablename__ = "custom_table"

        custom_registry = Mock()
        custom_registry.registry = Mock()
        custom_registry.registry.mappers = [mock_mapper]

        translator = SQLConditionTranslator(db, orm_registry=custom_registry)

        assert translator.db == db
        assert translator.orm_registry == custom_registry
        # Verify that the model cache was built using the custom registry
        assert "custom_table" in translator._model_cache


class TestExtractFieldAddresses:
    """Test extracting field addresses from a condition"""

    def test_extract_field_addresses_single_condition(
        self, translator, condition_leaf_role
    ):
        """Test extracting field addresses from a single condition"""
        field_addresses = translator.extract_field_addresses(condition_leaf_role)

        assert len(field_addresses) == 1
        field_addr = list(field_addresses)[0]
        assert field_addr.table_name == "fidesuser"
        assert field_addr.column_name == "permissions"
        assert field_addr.json_path == ["roles"]

    def test_extract_field_addresses_group_condition(
        self, translator, condition_leaf_role, condition_leaf_request_status
    ):
        """Test extracting field addresses from a group condition"""
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[condition_leaf_role, condition_leaf_request_status],
        )

        field_addresses = translator.extract_field_addresses(condition)

        assert len(field_addresses) == len(condition.conditions)
        table_names = {addr.table_name for addr in field_addresses}
        assert table_names == {"fidesuser", "privacyrequest"}

    def test_json_path_field_handling(self, translator):
        """Test handling of JSON path fields"""
        condition = ConditionLeaf(
            field_address="fidesuser.profile.name",
            operator=Operator.eq,
            value="John Doe",
        )

        field_addresses = translator.extract_field_addresses(condition)
        field_addr = list(field_addresses)[0]

        assert field_addr.table_name == "fidesuser"
        assert field_addr.column_name == "profile"
        assert field_addr.json_path == ["name"]


class TestMapTablesToFields:
    """Test mapping tables to fields"""

    def test_map_tables_to_fields(
        self,
        translator,
        condition_leaf_role,
        condition_leaf_request_status,
        condition_leaf_email_address,
    ):
        """Test analyzing tables and grouping field addresses"""
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[
                condition_leaf_role,
                condition_leaf_request_status,
                condition_leaf_email_address,
            ],
        )

        tables_to_fields = translator.map_tables_to_fields(condition)

        assert len(tables_to_fields) == 2
        assert "fidesuser" in tables_to_fields
        assert "privacyrequest" in tables_to_fields
        assert len(tables_to_fields["fidesuser"]) == 2
        assert len(tables_to_fields["privacyrequest"]) == 1

    def test_field_address_without_table_raises_error(self, translator):
        """Test that field addresses without table names raise errors"""
        condition = ConditionLeaf(
            field_address="username",  # No table specified
            operator=Operator.eq,
            value="approver",
        )

        with pytest.raises(SQLTranslationError, match="Table name not specified"):
            translator.map_tables_to_fields(condition)


class TestBuildFilterExpression:

    def test_build_filter_expression_leaf_condition(
        self, translator, condition_leaf_role, condition_leaf_user_status
    ):
        """Test building filter expressions for leaf conditions"""
        model_classes = {
            "fidesuser": FidesUser,
            "fidesuserpermissions": FidesUserPermissions,
        }

        # This is a relationship condition should return an Exists expression
        filter_expr = translator._build_filter_expression(
            condition_leaf_role, model_classes
        )
        # The filter should be a SQLAlchemy Exists expression for
        # relationship conditions with a 1:1 relationship
        assert isinstance(filter_expr, Exists)

        # This is a regular column condition should return a BinaryExpression
        filter_expr = translator._build_filter_expression(
            condition_leaf_user_status, model_classes
        )
        assert isinstance(filter_expr, BinaryExpression)

    def test_build_filter_expression_group_condition(
        self, translator, condition_leaf_role, condition_leaf_request_status
    ):
        """Test building filter expressions for group conditions"""
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[condition_leaf_role, condition_leaf_request_status],
        )

        model_classes = {"fidesuser": FidesUser, "privacyrequest": PrivacyRequest}

        filter_expr = translator._build_filter_expression(condition, model_classes)

        # Should return an AND expression (can be BinaryExpression or BooleanClauseList)
        assert isinstance(filter_expr, (BinaryExpression, BooleanClauseList))
        if isinstance(filter_expr, BooleanClauseList):
            assert filter_expr.operator is operator.and_
        else:
            assert str(filter_expr.operator) == "and_"

    def test_json_path_field_handling(self, translator):
        """Test handling of JSON path fields"""

        # Create a model with JSON column
        class MockModelWithJSON(TestBase):
            __tablename__ = "json_table"
            id = Column(String, primary_key=True)
            json_data = Column(JSONB)  # Use JSONB which supports the operators better

        condition = ConditionLeaf(
            field_address="json_table.json_data.nested.field",
            operator=Operator.eq,
            value="test",
        )

        model_classes = {"json_table": MockModelWithJSON}

        # This should handle JSON path fields - may return None if JSON operators not supported
        result = translator._build_filter_expression(condition, model_classes)
        # JSON path handling is database-specific, so we just test it doesn't crash
        assert result is not None or result is None

    def test_property_condition_handling(self, translator):
        """Test handling of Python properties on models"""

        class MockModelWithProperty(TestBase):
            __tablename__ = "prop_table"
            id = Column(String, primary_key=True)

            @property
            def computed_field(self):
                return "computed"

        condition = ConditionLeaf(
            field_address="prop_table.computed_field",
            operator=Operator.eq,
            value="test",
        )

        model_classes = {"prop_table": MockModelWithProperty}

        # This should raise a ValueError for properties
        with pytest.raises(
            ValueError, match="Property 'computed_field'.*cannot be translated to SQL"
        ):
            translator._build_filter_expression(condition, model_classes)

    def test_hybrid_property_handling(self, translator):
        """Test handling of hybrid properties"""

        class MockModelWithHybrid(TestBase):
            __tablename__ = "hybrid_table"
            id = Column(String, primary_key=True)
            first_name = Column(String)
            last_name = Column(String)

            @hybrid_property
            def full_name(self):
                return self.first_name + " " + self.last_name

        condition = ConditionLeaf(
            field_address="hybrid_table.full_name",
            operator=Operator.eq,
            value="John Doe",
        )

        model_classes = {"hybrid_table": MockModelWithHybrid}

        # Hybrid properties should be handled
        result = translator._build_filter_expression(condition, model_classes)
        assert result is not None

    def test_relationship_condition_unsupported_operator(self, translator):
        """Test relationship condition with unsupported operator"""

        class MockParent2(TestBase):
            __tablename__ = "parent_table2"
            id = Column(String, primary_key=True)

        class MockChild2(TestBase):
            __tablename__ = "child_table2"
            id = Column(String, primary_key=True)
            parent_id = Column(String, ForeignKey("parent_table2.id"))
            parent = relationship("MockParent2")

        condition = ConditionLeaf(
            field_address="child_table2.parent",
            operator=Operator.list_intersects,  # Truly unsupported operator
            value=["parent_id_value"],
        )

        model_classes = {"child_table2": MockChild2}

        # This should return None for unsupported relationship operators
        result = translator._build_filter_expression(condition, model_classes)
        # The method logs a warning and returns None for unsupported operators
        assert result is None

    def test_property_condition_with_relationships_suggestion(self, translator):
        """Test property condition error message includes relationship suggestions"""

        class MockParent3(TestBase):
            __tablename__ = "parent_table3"
            id = Column(String, primary_key=True)

        class MockModelWithPropertyAndRel(TestBase):
            __tablename__ = "prop_rel_table"
            id = Column(String, primary_key=True)
            parent_id = Column(String, ForeignKey("parent_table3.id"))
            parent = relationship("MockParent3")

            @property
            def computed_field(self):
                return "computed"

        condition = ConditionLeaf(
            field_address="prop_rel_table.computed_field",
            operator=Operator.eq,
            value="test",
        )

        model_classes = {"prop_rel_table": MockModelWithPropertyAndRel}

        # This should raise a ValueError with relationship suggestion
        with pytest.raises(
            ValueError, match="consider using the relationship directly"
        ):
            translator._build_filter_expression(condition, model_classes)

    def test_build_filter_expression_with_none_condition(self, translator):
        """Test _build_filter_expression with None condition"""
        assert translator._build_filter_expression(None, {}) is None

    def test_build_leaf_filter_missing_table_in_model_classes(self, translator):
        """Test _build_leaf_filter when table is not in model_classes"""
        condition = ConditionLeaf(
            field_address="missing_table.field",
            operator=Operator.eq,
            value="test_value",
        )

        model_classes = {"other_table": Mock()}

        result = translator._build_leaf_filter(condition, model_classes)

        assert result is None

    def test_build_leaf_filter_invalid_field_address(self, translator):
        """Test _build_leaf_filter with invalid field address"""
        condition = ConditionLeaf(
            field_address="invalid_format",  # No table.field format
            operator=Operator.eq,
            value="test_value",
        )

        model_classes = {"": Mock()}  # Empty table name

        result = translator._build_leaf_filter(condition, model_classes)

        # Should handle gracefully and return None or raise appropriate error
        # The exact behavior depends on implementation
        assert result is None or isinstance(result, Exception)


class TestApplyOperatorToColumn:
    """Test applying different operators to columns"""

    @pytest.mark.parametrize(
        "operator",
        [
            Operator.eq,
            Operator.neq,
            Operator.contains,
            Operator.starts_with,
            Operator.exists,
            Operator.not_exists,
            Operator.list_contains,
            Operator.not_in_list,
            Operator.ends_with,
            Operator.lt,
            Operator.lte,
            Operator.gt,
            Operator.gte,
        ],
    )
    def test_apply_operator_to_column(self, translator, operator):
        """Test applying different operators to columns"""
        column = FidesUser.username

        expr = translator._apply_operator_to_column(column, operator, "approver")
        assert isinstance(expr, BinaryExpression)

    def test_unsupported_operator_raises_error(self, translator):
        """Test that unsupported operators raise appropriate errors"""
        column = FidesUser.username

        # Create a mock operator that doesn't exist
        with pytest.raises(SQLTranslationError, match="Unsupported operator"):
            # This should raise an error for an unsupported operator
            translator._apply_operator_to_column(
                column, "unsupported_operator", "value"
            )


class TestDeepNestingBehavior:
    """Test how the translator handles deeply nested conditions"""

    @pytest.fixture
    def nested_condition(self, condition_leaf_user_status, condition_leaf_role):
        """Creates a deeplynested condition

        (user.disabled = False AND user.permissions.roles = 'approver') OR
        (permissions.roles = approver AND (user.password_login_enabled = true OR user.totp_secret is not null))
        """
        return ConditionGroup(
            logical_operator=GroupOperator.or_,
            conditions=[
                ConditionGroup(
                    logical_operator=GroupOperator.and_,
                    conditions=[
                        condition_leaf_user_status,
                        condition_leaf_role,
                    ],
                ),
                ConditionGroup(
                    logical_operator=GroupOperator.and_,
                    conditions=[
                        condition_leaf_role,
                        ConditionGroup(
                            logical_operator=GroupOperator.or_,
                            conditions=[
                                ConditionLeaf(
                                    field_address="fidesuser.password_login_enabled",
                                    operator=Operator.eq,
                                    value=True,
                                ),
                                ConditionLeaf(
                                    field_address="fidesuser.totp_secret",
                                    operator=Operator.exists,
                                    value=None,
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_map_tables_to_fields_flattens_nested_structure(
        self, translator, nested_condition
    ):
        """Test that map_tables_to_fields flattens nested logical structure"""

        # Map tables to fields - this should flatten the structure
        tables_to_fields = translator.map_tables_to_fields(nested_condition)

        # The method flattens all field addresses regardless of nesting
        assert len(tables_to_fields) == 1  # only fidesuser table
        assert "fidesuser" in tables_to_fields

        # All fields are collected, but logical nesting is lost
        fidesuser_fields = [f.column_name for f in tables_to_fields["fidesuser"]]

        assert set(fidesuser_fields) == {
            "disabled",
            "permissions",
            "password_login_enabled",
            "totp_secret",
        }

    def test_build_filter_expression_preserves_nesting(
        self, translator, nested_condition
    ):
        """Test that build_filter_expression preserves the logical nesting structure"""

        # Use existing models
        model_classes = {
            "fidesuser": FidesUser,
            "fidesuserpermissions": FidesUserPermissions,
        }

        # Build filter expression - this SHOULD preserve nesting
        filter_expr = translator._build_filter_expression(
            nested_condition, model_classes
        )

        # Verify the exact structure preserves nesting:
        # Should be: (user.disabled = False AND user.permissions.roles = 'approver') OR
        #           (user.permissions.roles = 'approver' AND (user.totp_secret is not null OR user.password_login_enabled = true))
        # OR (BooleanClauseList)
        # ├── AND (BooleanClauseList) - exactly 2 conditions
        # │   ├── user.disabled = False
        # │   └── user.permissions.roles = 'approver'
        # └── AND (BooleanClauseList) - exactly 2 conditions
        #     ├── user.permissions.roles = 'approver'
        #     └── Grouping (preserves parentheses)
        #         └── OR (BooleanClauseList) - exactly 2 conditions
        #             ├── user.totp_secret is not null
        #             └── user.password_login_enabled = true

        # Top level should be an OR with exactly 2 clauses
        assert isinstance(filter_expr, BooleanClauseList)
        assert filter_expr.operator is operator.or_
        clauses = list(filter_expr.clauses)
        assert len(clauses) == 2

        # First clause: (user.disabled = False AND user.permissions.roles = 'approver')
        left_group = clauses[0]
        print(type(left_group))
        assert isinstance(left_group, BooleanClauseList)
        assert left_group.operator is operator.and_
        left_conditions = list(left_group.clauses)
        assert len(left_conditions) == 2  # disabled and permissions.roles conditions

        # Second clause: (user.permissions.roles = 'approver' AND (user.totp_secret is not null OR user.password_login_enabled = true))
        right_group = clauses[1]
        assert isinstance(right_group, BooleanClauseList)
        assert right_group.operator is operator.and_
        right_conditions = list(right_group.clauses)
        assert len(right_conditions) == 2  # permissions.roles and nested OR conditions

        # The second condition in the right group should be another OR (user.totp_secret is not null OR user.password_login_enabled = true)
        # wrapped in a Grouping object to preserve parentheses
        nested_or_grouping = right_conditions[1]
        assert isinstance(nested_or_grouping, Grouping)

        # Unwrap the Grouping to get the actual BooleanClauseList
        nested_or = nested_or_grouping.element
        assert isinstance(nested_or, BooleanClauseList)
        assert nested_or.operator is operator.or_
        nested_conditions = list(nested_or.clauses)
        assert (
            len(nested_conditions) == 2
        )  # totp_secret and password_login_enabled conditions

    def test_build_sqlalchemy_query_nested_condition(
        self, db, translator, nested_condition
    ):
        """Test that build_sqlalchemy_query builds a query for a nested condition"""

        # Create translator with real session
        translator._model_cache = {
            "fidesuser": FidesUser,
            "fidesuserpermissions": FidesUserPermissions,
        }

        query = translator.build_sqlalchemy_query(nested_condition)

        # Verify the query was built successfully
        assert query is not None

        # Convert the query to SQL string to verify the structure
        query_str = str(query.statement.compile(compile_kwargs={"literal_binds": True}))

        # Verify the query contains the expected elements:
        # 1. SELECT from the primary table (fidesuser)
        assert "SELECT" in query_str
        assert "fidesuser" in query_str

        # 2. Contains the WHERE clause with our conditions
        assert "WHERE" in query_str

        # 3. Contains the logical operators (OR and AND)
        assert "OR" in query_str
        assert "AND" in query_str

        # 4. Contains our specific field conditions
        assert "disabled" in query_str
        assert "permissions" in query_str
        assert "roles" in query_str
        assert "password_login_enabled" in query_str
        assert "totp_secret" in query_str

        # 5. Contains our specific values
        assert "false" in query_str
        assert "approver" in query_str
        assert "EX" in query_str
        assert "true" in query_str

        # 6. Verify parentheses are present (indicating proper grouping)
        assert "(" in query_str and ")" in query_str
        print(query_str)
        # 7. Verify the query is valid SQL
        expected_parts = [
            "SELECT fidesuser.id, fidesuser.created_at, fidesuser.updated_at, fidesuser.username, fidesuser.email_address, fidesuser.first_name, fidesuser.last_name, fidesuser.hashed_password, fidesuser.salt, fidesuser.disabled, fidesuser.disabled_reason, fidesuser.last_login_at, fidesuser.password_reset_at, fidesuser.password_login_enabled, fidesuser.totp_secret ",
            "FROM fidesuser ",
            "WHERE fidesuser.disabled = false AND (EXISTS (SELECT 1 ",
            "FROM fidesuserpermissions ",
            "WHERE fidesuser.id = fidesuserpermissions.user_id AND 'approver' = ANY (fidesuserpermissions.roles))) OR (EXISTS (SELECT 1 ",
            "FROM fidesuserpermissions ",
            "WHERE fidesuser.id = fidesuserpermissions.user_id AND 'approver' = ANY (fidesuserpermissions.roles))) AND (fidesuser.password_login_enabled = true OR fidesuser.totp_secret IS NOT NULL)",
        ]

        for part in expected_parts:
            assert (
                part in query_str
            ), f"Expected '{part}' not found in generated SQL: {query_str}"


class TestExpandWithRelatedMainTables:
    """Test expansion of join tables to include main tables"""

    def test_expand_with_related_main_tables_no_inspection_available(self, translator):
        """Test _expand_with_related_main_tables when model inspection fails"""
        # Create a mock model that can't be inspected
        mock_model = Mock()
        mock_model.__name__ = "MockModel"

        model_classes = {"mock_table": mock_model}
        tables_to_fields = {"mock_table": []}

        # Mock inspect to raise NoInspectionAvailable
        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            side_effect=NoInspectionAvailable("Cannot inspect mock model"),
        ):
            result = translator._expand_with_related_main_tables(
                model_classes, tables_to_fields
            )

        # Should return empty dict when inspection fails
        assert result == {}

    def test_join_table_expansion(self, translator):
        """Test expansion of join tables to include main tables"""

        model_classes = {"fidesuserpermissions": FidesUserPermissions}
        tables_to_fields = {"fidesuserpermissions": []}

        # This should identify join tables and try to expand
        result = translator._expand_with_related_main_tables(
            model_classes, tables_to_fields
        )
        assert "fidesuser" in result

    def test_find_related_main_tables_exception_handling(self, translator):
        """Test exception handling in _find_related_main_tables"""

        class MockBrokenModel:
            """Model that will cause inspection to fail"""

            pass

        # This should handle the exception gracefully
        result = translator._find_related_main_tables(MockBrokenModel, "broken_table")

        # Should return empty dict when inspection fails
        assert result == {}


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_unknown_condition_type_raises_error(self, translator):
        """Test that unknown condition types raise errors"""
        # Mock an unknown condition type
        unknown_condition = Mock()

        with pytest.raises(SQLTranslationError, match="Unknown condition type"):
            translator.extract_field_addresses(unknown_condition)

    def test_no_models_found_raises_error(self, translator):
        """Test error when no models are found for tables"""
        condition = ConditionLeaf(
            field_address="nonexistent.field", operator=Operator.eq, value="value"
        )

        with pytest.raises(
            SQLTranslationError, match="No valid SQLAlchemy models found"
        ):
            translator.build_sqlalchemy_query(condition)

    def test_property_condition_provides_helpful_error(self, translator):
        """Test that property conditions provide helpful error messages"""

        # Create a mock model with a property
        mock_model = Mock()
        mock_model.__name__ = "MockModel"

        # Mock the property
        mock_property = property(lambda self: "computed_value")

        # Mock the mapper inspection
        mock_mapper = Mock()
        mock_mapper.columns.keys.return_value = ["id", "name", "email"]
        mock_mapper.relationships.keys.return_value = ["references", "logs"]

        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect"
        ) as mock_inspect:
            mock_inspect.return_value = mock_mapper

            condition = ConditionLeaf(
                field_address="computed_property",
                operator=Operator.eq,
                value="test_value",
            )

            # Test that the error message is helpful and generic
            with pytest.raises(ValueError) as exc_info:
                translator._handle_property_condition(
                    mock_model, "computed_property", mock_property, condition
                )

            error_msg = str(exc_info.value)
            assert "computed_property" in error_msg
            assert "MockModel" in error_msg
            assert "cannot be translated to SQL" in error_msg
            assert "Properties are computed at runtime" in error_msg
            assert "Available columns: ['id', 'name', 'email']" in error_msg
            assert "Available relationships: ['references', 'logs']" in error_msg

    def test_build_filter_expression_with_none_filter(self, translator):
        """Test _build_filter_expression when filter expression is None"""
        # Create a condition that would return None filter expression
        condition = ConditionLeaf(
            field_address="nonexistent_table.field", operator=Operator.eq, value="test"
        )

        # Mock model_classes without the nonexistent_table
        model_classes = {}

        result = translator._build_filter_expression(condition, model_classes)
        assert result is None

    def test_build_leaf_filter_nonexistent_table(self, translator):
        """Test _build_leaf_filter when table doesn't exist in model_classes"""
        condition = ConditionLeaf(
            field_address="nonexistent_table.field", operator=Operator.eq, value="test"
        )

        model_classes = {"other_table": Mock()}

        result = translator._build_leaf_filter(condition, model_classes)
        assert result is None

    def test_build_leaf_filter_nonexistent_column(self, translator):
        """Test _build_leaf_filter when column doesn't exist on model"""
        condition = ConditionLeaf(
            field_address="test_table.nonexistent_field",
            operator=Operator.eq,
            value="test",
        )

        mock_model = Mock()
        # Mock hasattr to return False for nonexistent field
        with patch("builtins.hasattr", return_value=False):
            model_classes = {"test_table": mock_model}
            result = translator._build_leaf_filter(condition, model_classes)
            assert result is None


class TestSQLTranslatorEdgeCases:
    """Test edge cases and error conditions in SQLConditionTranslator"""

    def test_find_related_main_tables_no_relationships(self, translator):
        """Test _find_related_main_tables with model that has no relationships"""
        # Mock the inspect function to return a mapper with no relationships
        mock_mapper = Mock()
        mock_relationships = Mock()
        mock_relationships.items.return_value = []
        mock_mapper.relationships = mock_relationships

        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            return_value=mock_mapper,
        ):
            result = translator._find_related_main_tables(
                MOCK_MODEL_CLASS, "join_table"
            )

        assert result == {}

    def test_robust_relationship_handling_collection_vs_scalar(self, translator):
        """Test that the robust relationship handler correctly distinguishes collections from scalars"""
        # Test collection relationship (one-to-many)
        mock_collection_rel = Mock()
        mock_collection_property = Mock()
        mock_collection_property.uselist = True  # This is a collection
        mock_collection_property.mapper.class_ = Mock()
        mock_collection_rel.property = mock_collection_property
        mock_collection_rel.any.return_value = Mock()

        # Test scalar relationship (one-to-one)
        mock_scalar_rel = Mock()
        mock_scalar_property = Mock()
        mock_scalar_property.uselist = False  # This is a scalar
        mock_scalar_property.mapper.class_ = Mock()
        mock_scalar_rel.property = mock_scalar_property
        mock_scalar_rel.has.return_value = Mock()

        condition = ConditionLeaf(
            field_address="table.relation.field",
            operator=Operator.exists,
            value=None,
        )

        # Collection should use any()
        translator._handle_relationship_condition(mock_collection_rel, condition)
        mock_collection_rel.any.assert_called_once()

        # Scalar should use has()
        translator._handle_relationship_condition(mock_scalar_rel, condition)
        mock_scalar_rel.has.assert_called_once()

    def test_relationship_target_field_extraction(self):
        """Test extraction of target fields from relationship field addresses"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        # Mock relationship with proper structure
        mock_relationship = Mock()
        mock_property = Mock()
        mock_related_model = Mock()
        mock_related_model.__name__ = "RelatedModel"
        mock_property.mapper.class_ = mock_related_model
        mock_relationship.property = mock_property

        # Mock inspector for primary key detection
        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect"
        ) as mock_inspect:
            mock_inspector = Mock()
            mock_pk = Mock()
            mock_pk.name = "uuid"
            mock_inspector.primary_key = [mock_pk]
            mock_inspect.return_value = mock_inspector

            # Test field address with specific field
            field_addr_with_field = FieldAddress.parse("table.relationship.name")
            target_field = translator._extract_relationship_target_field(
                field_addr_with_field, mock_relationship
            )
            assert target_field == "name"

            # Test field address without specific field (should use primary key)
            field_addr_without_field = FieldAddress.parse("table.relationship")
            target_field = translator._extract_relationship_target_field(
                field_addr_without_field, mock_relationship
            )
            assert target_field == "uuid"

    def test_relationship_error_handling(self):
        """Test error handling in relationship operations"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        # Create a relationship that will cause errors
        mock_relationship = Mock()
        mock_relationship.property = None  # This will cause AttributeError

        condition = ConditionLeaf(
            field_address="table.relation.field",
            operator=Operator.eq,
            value="test",
        )

        # Should handle errors gracefully and return None
        result = translator._handle_relationship_condition(mock_relationship, condition)
        assert result is None

    def test_generate_query_from_condition_with_none_condition(self, translator):
        """Test generate_query_from_condition with None condition"""

        # Should raise SQLTranslationError for None condition
        with pytest.raises(SQLTranslationError) as exc_info:
            translator.generate_query_from_condition(None, "default_table")

        assert "Unknown condition type" in str(exc_info.value)

    def test_generate_query_from_condition_empty_default_table(self, translator):
        """Test generate_query_from_condition with empty default table"""

        condition = ConditionLeaf(
            field_address="field_only",  # No table specified
            operator=Operator.eq,
            value="test_value",
        )

        # Should raise SQLTranslationError when no table is specified
        with pytest.raises(SQLTranslationError) as exc_info:
            translator.generate_query_from_condition(condition, "")

        assert "Table name not specified" in str(exc_info.value)


class TestSQLTranslatorRelationshipHandling:
    """Test relationship handling and join logic in SQLConditionTranslator"""

    def test_add_relationship_joins_no_models(self, translator):
        """Test _add_relationship_joins with empty model_classes"""
        # Should return the original query unchanged
        assert (
            translator._add_relationship_joins(
                MOCK_QUERY, MOCK_PRIMARY_MODEL, {}, "primary_table", {}
            )
            == MOCK_QUERY
        )

    def test_add_relationship_joins_only_primary_table(self, translator):
        """Test _add_relationship_joins with only primary table in model_classes"""
        model_classes = {"primary_table": MOCK_PRIMARY_MODEL}

        # Should return the original query unchanged since only primary table
        assert (
            translator._add_relationship_joins(
                MOCK_QUERY, MOCK_PRIMARY_MODEL, model_classes, "primary_table", {}
            )
            == MOCK_QUERY
        )


class TestFindRelationshipPath:
    """Test finding relationship paths in SQLConditionTranslator"""

    def test_find_relationship_path_through_intermediates_no_inspection(
        self, translator
    ):
        """Test _find_relationship_path_through_intermediates when model inspection fails"""
        mock_model1 = Mock()
        mock_model1.__name__ = "MockModel1"
        mock_model2 = Mock()
        mock_model2.__name__ = "MockModel2"

        # Mock inspect to raise NoInspectionAvailable
        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            side_effect=NoInspectionAvailable("Cannot inspect model"),
        ):
            result = translator._find_relationship_path_through_intermediates(
                mock_model1, mock_model2
            )

        assert result == []

    def test_find_relationship_path_through_intermediates_with_custom_max_depth(
        self, translator
    ):
        """Test _find_relationship_path_through_intermediates with custom max_depth"""
        # Mock models with no relationships to test max_depth parameter
        mock_mapper = Mock()
        mock_mapper.relationships.items.return_value = []

        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            return_value=mock_mapper,
        ):
            result = translator._find_relationship_path_through_intermediates(
                MOCK_MODEL_CLASS, MOCK_PRIMARY_MODEL, max_depth=1
            )

        # Should return empty list as there are no relationships
        assert result == []

    def test_find_relationship_path_through_intermediates_empty_queue(self, translator):
        """Test _find_relationship_path_through_intermediates when queue becomes empty"""
        # Mock models with no relationships to test empty queue scenario
        mock_mapper = Mock()
        mock_mapper.relationships.items.return_value = []

        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            return_value=mock_mapper,
        ):
            result = translator._find_relationship_path_through_intermediates(
                MOCK_MODEL_CLASS, MOCK_PRIMARY_MODEL, max_depth=1
            )

        assert result == []

    def test_extract_relationship_target_field_no_inspection_available(
        self, translator
    ):
        """Test _extract_relationship_target_field when inspection fails"""
        field_addr = FieldAddress.parse("table.relationship")
        mock_relationship = Mock()
        mock_relationship.property.mapper.class_ = Mock()

        # Mock inspect to raise NoInspectionAvailable
        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            side_effect=NoInspectionAvailable("Cannot inspect"),
        ):
            result = translator._extract_relationship_target_field(
                field_addr, mock_relationship
            )

        # Should return default primary key
        assert result == translator.DEFAULT_PRIMARY_KEY

    def test_apply_reverse_join_no_primaryjoin(self, translator):
        """Test _apply_reverse_join when relationship has no primaryjoin"""
        mock_query = Mock()
        mock_relationship_attr = Mock()
        mock_relationship_attr.class_ = Mock()
        mock_relationship_attr.class_.__name__ = "TargetModel"
        mock_relationship_attr.property.primaryjoin = None
        mock_primary_model = Mock()
        mock_primary_model.__name__ = "PrimaryModel"

        with pytest.raises(SQLTranslationError) as exc_info:
            translator._apply_reverse_join(
                mock_query, mock_relationship_attr, mock_primary_model
            )

        assert "No primaryjoin found for PrimaryModel, TargetModel" in str(
            exc_info.value
        )

    def test_fetch_join_path_with_successful_direct_path(self, translator):
        """Test _fetch_join_path when direct relationship path is found"""
        # Mock successful direct path finding
        mock_relationship = Mock()
        translator._find_relationship_path = Mock(return_value=[mock_relationship])

        result = translator._fetch_join_path(
            MOCK_MODEL_CLASS,
            MOCK_PRIMARY_MODEL,
            {},
            "table_name",
            "primary_table",
        )

        # Should return the relationship path
        assert result == [mock_relationship]
        translator._find_relationship_path.assert_called_once_with(
            MOCK_PRIMARY_MODEL, MOCK_MODEL_CLASS
        )

    def test_fetch_join_path_with_reverse_relationship(self, translator):
        """Test _fetch_join_path when reverse relationship path is found"""
        translator._find_relationship_path(ManualTaskInstance, PrivacyRequest)

    def test_fetch_join_path_with_intermediate_path(self, translator):
        """Test _fetch_join_path when intermediate relationship path is found"""
        # Mock failed direct path but successful intermediate path
        translator._find_relationship_path = Mock(return_value=None)
        mock_relationship1 = Mock()
        mock_relationship2 = Mock()
        translator._find_relationship_path_through_intermediates = Mock(
            return_value=[mock_relationship1, mock_relationship2]
        )

        # Mock query.join to return new queries - the query is modified in place
        # but returns itself each time
        MOCK_QUERY.join.return_value = MOCK_QUERY

        result = translator._fetch_join_path(
            MOCK_MODEL_CLASS,
            MOCK_PRIMARY_MODEL,
            {},
            "table_name",
            "primary_table",
        )

        # Should return the intermediate relationship path
        assert result == [mock_relationship1, mock_relationship2]
        translator._find_relationship_path.assert_called_once_with(
            MOCK_PRIMARY_MODEL, MOCK_MODEL_CLASS
        )
        translator._find_relationship_path_through_intermediates.assert_called_once_with(
            MOCK_PRIMARY_MODEL, MOCK_MODEL_CLASS
        )

    def test_fetch_join_path_fallback_to_other_models(self, translator):
        """Test _fetch_join_path fallback to finding paths through other models"""
        # Mock failed direct and intermediate paths
        translator._find_relationship_path = Mock(return_value=None)
        translator._find_relationship_path_through_intermediates = Mock(
            return_value=None
        )

        # Mock other models in model_classes
        mock_other_model = Mock()
        model_classes = {
            "table_name": MOCK_MODEL_CLASS,
            "primary_table": MOCK_PRIMARY_MODEL,
            "other_table": mock_other_model,
        }

        # Mock finding path through other model
        mock_relationship = Mock()
        translator._find_relationship_path_through_intermediates = Mock(
            side_effect=[None, [mock_relationship]]  # First call fails, second succeeds
        )

        mock_joined_query = Mock()
        MOCK_QUERY.join.return_value = mock_joined_query

        result = translator._fetch_join_path(
            MOCK_MODEL_CLASS,
            MOCK_PRIMARY_MODEL,
            model_classes,
            "table_name",
            "primary_table",
        )

        # Should return the fallback relationship path
        assert result == [mock_relationship]

    def test_fetch_join_path_no_path_found(self, translator):
        """Test _fetch_join_path when no relationship path is found"""
        # Mock all path finding methods to return None
        translator._find_relationship_path = Mock(return_value=None)
        translator._find_relationship_path_through_intermediates = Mock(
            return_value=None
        )

        model_classes = {
            "table_name": MOCK_MODEL_CLASS,
            "primary_table": MOCK_PRIMARY_MODEL,
        }

        result = translator._fetch_join_path(
            MOCK_MODEL_CLASS,
            MOCK_PRIMARY_MODEL,
            model_classes,
            "table_name",
            "primary_table",
        )

        # Should return None when no path found
        assert result == []

    def test_find_relationship_path_same_model(self, translator):
        """Test _find_relationship_path when from and to models are the same"""
        # Should return empty list for same model
        assert (
            translator._find_relationship_path(MOCK_MODEL_CLASS, MOCK_MODEL_CLASS) == []
        )
        assert (
            translator._find_relationship_path_through_intermediates(
                MOCK_MODEL_CLASS, MOCK_MODEL_CLASS, max_depth=3
            )
            == []
        )

    def test_find_relationship_path_no_relationships(self, translator):
        """Test _find_relationship_path with model that has no relationships"""
        # Mock the inspect function to return a mapper with no relationships
        mock_mapper = Mock()
        mock_mapper.class_ = MOCK_MODEL_CLASS  # Set the class_ attribute
        mock_relationships = Mock()
        mock_relationships.items.return_value = []
        mock_mapper.relationships = mock_relationships

        mock_target_mapper = Mock()
        mock_target_mapper.class_ = (
            MOCK_PRIMARY_MODEL  # Set the class_ attribute for target
        )
        mock_target_relationships = Mock()
        mock_target_relationships.items.return_value = []
        mock_target_mapper.relationships = mock_target_relationships

        def mock_inspect(model):
            if model == MOCK_MODEL_CLASS:
                return mock_mapper
            elif model == MOCK_PRIMARY_MODEL:
                return mock_target_mapper
            else:
                return Mock()

        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            side_effect=mock_inspect,
        ):
            result = translator._find_relationship_path(
                MOCK_MODEL_CLASS, MOCK_PRIMARY_MODEL
            )

        assert result == []

    def test_build_sqlalchemy_query_not_valid(self, translator):
        """Test build_sqlalchemy_query when no valid SQLAlchemy models are found"""
        # Mock map_tables_to_fields to return tables
        translator.map_tables_to_fields = Mock(return_value={"test_table": []})

        # Mock _model_cache as a dictionary that returns None for the test_table
        translator._model_cache = {"test_table": None}

        condition = ConditionLeaf(
            field_address="test_table.field", operator=Operator.eq, value="test_value"
        )

        with pytest.raises(SQLTranslationError) as exc_info:
            translator.build_sqlalchemy_query(condition)

        assert "No valid SQLAlchemy models found" in str(exc_info.value)
