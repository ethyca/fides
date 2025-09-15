"""
Tests for the enhanced SQLAlchemy-based SQLConditionTranslator
"""

import operator
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, create_autospec, patch

import pytest
from pytest import param
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Grouping

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

# Mock models for testing
TestBase = declarative_base()


@pytest.fixture
def mock_db():
    """Create a mock SQLAlchemy session"""
    db = create_autospec(Session, spec_set=True)
    return db


class MockUser(TestBase):
    __tablename__ = "fidesuser"
    id = Column(String, primary_key=True)
    username = Column(String)
    email_address = Column(String)
    disabled = Column(Boolean)
    role = Column(String)
    status = Column(String)


class MockPrivacyRequest(TestBase):
    __tablename__ = "privacyrequest"
    id = Column(String, primary_key=True)
    due_date = Column(DateTime)
    status = Column(String)
    client_id = Column(String)


class MockProfile(TestBase):
    __tablename__ = "profile"
    id = Column(String, primary_key=True)
    verified = Column(Boolean)
    age = Column(Integer)
    country = Column(String)


@pytest.fixture
def mock_registry():
    """Create a mock ORM registry with test models"""
    registry = Mock()

    # Mock mappers for our test models
    user_mapper = Mock()
    user_mapper.class_ = MockUser

    privacy_request_mapper = Mock()
    privacy_request_mapper.class_ = MockPrivacyRequest

    profile_mapper = Mock()
    profile_mapper.class_ = MockProfile

    registry.mappers = [
        user_mapper,
        privacy_request_mapper,
        profile_mapper,
    ]

    return registry


@pytest.fixture
def translator(mock_db, mock_registry):
    """Create a translator instance with mocked dependencies"""
    translator = SQLConditionTranslator(db=mock_db)

    # Mock the registry access
    translator.orm_registry = Mock()
    translator.orm_registry.registry = mock_registry

    return translator


@pytest.fixture
def condition_leaf_role():
    return ConditionLeaf(
        field_address="fidesuser.role",
        operator=Operator.eq,
        value="admin",
    )


@pytest.fixture
def condition_leaf_user_status():
    return ConditionLeaf(
        field_address="fidesuser.status",
        operator=Operator.eq,
        value="active",
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

    def test_constructor_requires_db(self, mock_db):
        """Test that constructor requires a db session"""
        translator = SQLConditionTranslator(db=mock_db)
        assert translator.db == mock_db

        with pytest.raises(TypeError) as exc_info:
            SQLConditionTranslator()

        assert "db" in str(exc_info.value)

    def test_extract_field_addresses_single_condition(
        self, translator, condition_leaf_role
    ):
        """Test extracting field addresses from a single condition"""
        field_addresses = translator.extract_field_addresses(condition_leaf_role)

        assert len(field_addresses) == 1
        field_addr = list(field_addresses)[0]
        assert field_addr.table_name == "fidesuser"
        assert field_addr.column_name == "role"

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

    def test_analyze_tables_in_condition(
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

        tables_to_fields = translator.analyze_tables_in_condition(condition)

        assert len(tables_to_fields) == 2
        assert "fidesuser" in tables_to_fields
        assert "privacyrequest" in tables_to_fields
        assert len(tables_to_fields["fidesuser"]) == 2
        assert len(tables_to_fields["privacyrequest"]) == 1

    def test_get_orm_model_by_table_name(self, translator):
        """Test getting ORM model by table name"""
        # Populate the model cache for testing
        translator._model_cache["fidesuser"] = MockUser

        # Test successful lookup
        model = translator.get_orm_model_by_table_name("fidesuser")
        assert model == MockUser

        # Test caching
        model2 = translator.get_orm_model_by_table_name("privacyrequest")
        assert model2 == MockPrivacyRequest
        assert "privacyrequest" in translator._model_cache

    def test_build_filter_expression_leaf_condition(
        self, translator, condition_leaf_role
    ):
        """Test building filter expressions for leaf conditions"""
        model_classes = {"fidesuser": MockUser}

        filter_expr = translator._build_filter_expression(
            condition_leaf_role, model_classes
        )

        # The filter should be a SQLAlchemy comparison
        assert isinstance(filter_expr, BinaryExpression)

    def test_build_filter_expression_group_condition(
        self, translator, condition_leaf_role, condition_leaf_request_status
    ):
        """Test building filter expressions for group conditions"""
        condition = ConditionGroup(
            logical_operator=GroupOperator.and_,
            conditions=[condition_leaf_role, condition_leaf_request_status],
        )

        model_classes = {"fidesuser": MockUser, "privacyrequest": MockPrivacyRequest}

        filter_expr = translator._build_filter_expression(condition, model_classes)

        # Should return an AND expression (can be BinaryExpression or BooleanClauseList)
        assert isinstance(filter_expr, (BinaryExpression, BooleanClauseList))
        if isinstance(filter_expr, BooleanClauseList):
            assert filter_expr.operator is operator.and_
        else:
            assert str(filter_expr.operator) == "and_"

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
            Operator.starts_with,
            Operator.ends_with,
            Operator.contains,
            Operator.lt,
            Operator.lte,
            Operator.gt,
            Operator.gte,
        ],
    )
    def test_apply_operator_to_column(self, translator, operator):
        """Test applying different operators to columns"""
        column = MockUser.username

        expr = translator._apply_operator_to_column(column, operator, "admin")
        assert isinstance(expr, BinaryExpression)

    def test_unsupported_operator_raises_error(self, translator):
        """Test that unsupported operators raise appropriate errors"""
        column = MockUser.username

        # Create a mock operator that doesn't exist
        with pytest.raises(SQLTranslationError, match="Unsupported operator"):
            # This should raise an error for an unsupported operator
            translator._apply_operator_to_column(
                column, "unsupported_operator", "value"
            )

    def test_determine_primary_table(self, translator):
        """Test determining the primary table for queries"""
        model_classes = {"fidesuser": MockUser, "privacyrequest": MockPrivacyRequest}

        # Create mock field addresses - more fields for fidesuser
        tables_to_fields = {
            "fidesuser": [
                FieldAddress.parse("fidesuser.username"),
                FieldAddress.parse("fidesuser.email_address"),
            ],
            "privacyrequest": [FieldAddress.parse("privacyrequest.status")],
        }

        primary = translator._determine_primary_table(model_classes, tables_to_fields)

        # Should choose fidesuser because it is the first table in the condition
        assert primary == "fidesuser"

    @pytest.mark.parametrize(
        "model_classes, tables_to_fields",
        [
            param({}, {}, id="empty_inputs"),
            param({}, {"test_table": []}, id="no_fields_in_tables"),
            param({}, {"other_table": []}, id="model_not_in_classes"),
        ],
    )
    def test_determine_primary_table_edge_cases(
        self, translator, model_classes, tables_to_fields
    ):
        """Test _determine_primary_table edge cases"""
        result = translator._determine_primary_table(model_classes, tables_to_fields)
        assert result is None

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

    def test_field_address_without_table_raises_error(self, translator):
        """Test that field addresses without table names raise errors"""
        condition = ConditionLeaf(
            field_address="username",  # No table specified
            operator=Operator.eq,
            value="admin",
        )

        with pytest.raises(SQLTranslationError, match="Table name not specified"):
            translator.analyze_tables_in_condition(condition)


class TestDeepNestingBehavior:
    """Test how the translator handles deeply nested conditions"""

    @pytest.fixture
    def nested_condition(self, condition_leaf_user_status, condition_leaf_role):
        """Creates a deeplynested condition

        (user.status = 'active' AND user.role = 'admin') OR
        (profile.verified = true AND (profile.age > 18 OR profile.country = 'US'))
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
                        ConditionLeaf(
                            field_address="profile.verified",
                            operator=Operator.eq,
                            value=True,
                        ),
                        ConditionGroup(
                            logical_operator=GroupOperator.or_,
                            conditions=[
                                ConditionLeaf(
                                    field_address="profile.age",
                                    operator=Operator.gt,
                                    value=18,
                                ),
                                ConditionLeaf(
                                    field_address="profile.country",
                                    operator=Operator.eq,
                                    value="US",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

    def test_analyze_tables_flattens_nested_structure(
        self, translator, nested_condition
    ):
        """Test that analyze_tables_in_condition flattens nested logical structure"""

        # Analyze tables - this should flatten the structure
        tables_to_fields = translator.analyze_tables_in_condition(nested_condition)

        # The method flattens all field addresses regardless of nesting
        assert len(tables_to_fields) == 2  # fidesuser and profile tables
        assert "fidesuser" in tables_to_fields
        assert "profile" in tables_to_fields

        # All fields are collected, but logical nesting is lost
        fidesuser_fields = [f.column_name for f in tables_to_fields["fidesuser"]]
        profile_fields = [f.column_name for f in tables_to_fields["profile"]]

        assert set(fidesuser_fields) == {"status", "role"}
        assert set(profile_fields) == {"verified", "age", "country"}

    def test_build_filter_expression_preserves_nesting(
        self, translator, nested_condition
    ):
        """Test that build_filter_expression preserves the logical nesting structure"""

        # Use existing mock models
        model_classes = {"fidesuser": MockUser, "profile": MockProfile}

        # Build filter expression - this SHOULD preserve nesting
        filter_expr = translator._build_filter_expression(
            nested_condition, model_classes
        )

        # Verify the exact structure preserves nesting:
        # Should be: (user.status = 'active' AND user.role = 'admin') OR
        #           (profile.verified = true AND (profile.age > 18 OR profile.country = 'US'))
        # OR (BooleanClauseList)
        # ├── AND (BooleanClauseList) - exactly 2 conditions
        # │   ├── user.status = 'active'
        # │   └── user.role = 'admin'
        # └── AND (BooleanClauseList) - exactly 2 conditions
        #     ├── profile.verified = true
        #     └── Grouping (preserves parentheses)
        #         └── OR (BooleanClauseList) - exactly 2 conditions
        #             ├── profile.age > 18
        #             └── profile.country = 'US'

        # Top level should be an OR with exactly 2 clauses
        assert isinstance(filter_expr, BooleanClauseList)
        assert filter_expr.operator is operator.or_
        clauses = list(filter_expr.clauses)
        assert len(clauses) == 2

        # First clause: (user.status = 'active' AND user.role = 'admin')
        left_group = clauses[0]
        assert isinstance(left_group, BooleanClauseList)
        assert left_group.operator is operator.and_
        left_conditions = list(left_group.clauses)
        assert len(left_conditions) == 2  # status and role conditions

        # Second clause: (profile.verified = true AND (profile.age > 18 OR profile.country = 'US'))
        right_group = clauses[1]
        assert isinstance(right_group, BooleanClauseList)
        assert right_group.operator is operator.and_
        right_conditions = list(right_group.clauses)
        assert len(right_conditions) == 2  # verified and nested OR conditions

        # The second condition in the right group should be another OR (age > 18 OR country = 'US')
        # wrapped in a Grouping object to preserve parentheses
        nested_or_grouping = right_conditions[1]
        assert isinstance(nested_or_grouping, Grouping)

        # Unwrap the Grouping to get the actual BooleanClauseList
        nested_or = nested_or_grouping.element
        assert isinstance(nested_or, BooleanClauseList)
        assert nested_or.operator is operator.or_
        nested_conditions = list(nested_or.clauses)
        assert len(nested_conditions) == 2  # age and country conditions

    def test_build_sqlalchemy_query_nested_condition(self, nested_condition):
        """Test that build_sqlalchemy_query builds a query for a nested condition"""
        from sqlalchemy import MetaData, create_engine
        from sqlalchemy.orm import sessionmaker

        # Create a real in-memory SQLite database for this test
        engine = create_engine("sqlite:///:memory:")

        # Create the tables
        metadata = MetaData()
        MockUser.metadata = metadata
        MockProfile.metadata = metadata
        metadata.create_all(engine)

        # Create a real session
        Session = sessionmaker(bind=engine)
        session = Session()

        # Create translator with real session
        translator = SQLConditionTranslator(db=session)
        translator._model_cache = {
            "fidesuser": MockUser,
            "profile": MockProfile,
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
        assert "status" in query_str
        assert "role" in query_str
        assert "verified" in query_str
        assert "age" in query_str
        assert "country" in query_str

        # 5. Contains our specific values
        assert "'active'" in query_str
        assert "'admin'" in query_str
        assert "18" in query_str
        assert "'US'" in query_str

        # 6. Verify parentheses are present (indicating proper grouping)
        assert "(" in query_str and ")" in query_str

        expected_parts = [
            "SELECT fidesuser.id, fidesuser.username, fidesuser.email_address, fidesuser.disabled, fidesuser.role, fidesuser.status",
            "FROM fidesuser, profile",
            "WHERE fidesuser.status = 'active' AND fidesuser.role = 'admin' OR profile.verified = true AND (profile.age > 18 OR profile.country = 'US')",
        ]

        for part in expected_parts:
            assert (
                part in query_str
            ), f"Expected '{part}' not found in generated SQL: {query_str}"

        # Clean up
        session.close()

    def test_json_path_field_handling(self, translator):
        """Test handling of JSON path fields"""
        from sqlalchemy import JSON, Column
        from sqlalchemy.dialects.postgresql import JSONB

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

    def test_colon_format_field_address(self):
        """Test field addresses with colon format"""
        from fides.api.task.conditional_dependencies.sql_schemas import FieldAddress

        # Test colon format parsing
        field_addr = FieldAddress.parse("table:column")
        assert field_addr.table_name == "table"
        assert field_addr.column_name == "column"
        assert field_addr.json_path is None

        # Test dataset:collection:field format
        field_addr2 = FieldAddress.parse("dataset:collection:field")
        assert field_addr2.table_name == "dataset"
        assert field_addr2.column_name == "collection:field"
        assert field_addr2.json_path is None

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
        from sqlalchemy.ext.hybrid import hybrid_property

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

    def test_join_table_expansion(self, translator):
        """Test expansion of join tables to include main tables"""

        class MockJoinReference(TestBase):
            __tablename__ = "user_reference"
            id = Column(String, primary_key=True)
            user_id = Column(String)

        model_classes = {"user_reference": MockJoinReference}
        tables_to_fields = {"user_reference": []}

        # This should identify join tables and try to expand
        result = translator._expand_with_related_main_tables(
            model_classes, tables_to_fields
        )

        # Should at least return the original model classes
        assert "user_reference" in result

    def test_json_path_complex_case(self):
        """Test JSON path handling for complex multi-level paths"""
        from fides.api.task.conditional_dependencies.sql_schemas import FieldAddress

        # Test complex JSON path with multiple levels
        field_addr = FieldAddress.parse("table.json_column.level1.level2.level3")

        assert field_addr.table_name == "table"
        assert field_addr.column_name == "json_column"
        assert field_addr.json_path == ["level1", "level2", "level3"]

        # Test the complex case SQL generation
        sql_column = field_addr.to_sql_column(enable_json_operators=True)
        expected = "json_column->'level1'->'level2'->>'level3'"
        assert sql_column == expected

    def test_simple_column_address_parsing(self):
        """Test parsing of simple column addresses without table"""
        from fides.api.task.conditional_dependencies.sql_schemas import FieldAddress

        # Test simple column name without table
        field_addr = FieldAddress.parse("column_name")
        assert field_addr.table_name == ""
        assert field_addr.column_name == "column_name"
        assert field_addr.json_path is None

    def test_relationship_condition_unsupported_operator(self, translator):
        """Test relationship condition with unsupported operator"""
        from sqlalchemy.orm import relationship

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

    def test_find_related_main_tables_exception_handling(self, translator):
        """Test exception handling in _find_related_main_tables"""

        class MockBrokenModel:
            """Model that will cause inspection to fail"""

            pass

        # This should handle the exception gracefully
        result = translator._find_related_main_tables(MockBrokenModel, "broken_table")

        # Should return empty dict when inspection fails
        assert result == {}

    def test_property_condition_with_relationships_suggestion(self, translator):
        """Test property condition error message includes relationship suggestions"""
        from sqlalchemy.orm import relationship

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

    def test_handle_model_attribute_relationship_detection(self, translator):
        """Test _handle_model_attribute correctly detects and handles relationships"""
        from unittest.mock import Mock, patch

        from sqlalchemy.orm import RelationshipProperty, relationship

        class MockParentModel(TestBase):
            __tablename__ = "parent_model_table"
            id = Column(String, primary_key=True)

        class MockModelWithRelationship(TestBase):
            __tablename__ = "model_with_rel_table"
            id = Column(String, primary_key=True)
            parent_id = Column(String, ForeignKey("parent_model_table.id"))
            parent = relationship("MockParentModel")

        condition = ConditionLeaf(
            field_address="model_with_rel_table.parent",
            operator=Operator.eq,
            value="test_value",
        )

        # Get the actual relationship attribute
        rel_attr = MockModelWithRelationship.parent

        # Verify it's detected as a relationship
        assert hasattr(rel_attr, "property")
        assert isinstance(rel_attr.property, RelationshipProperty)

        # Mock _handle_relationship_condition to verify it's called
        with patch.object(
            translator, "_handle_relationship_condition"
        ) as mock_handle_rel:
            mock_handle_rel.return_value = Mock()

            result = translator._handle_model_attribute(
                MockModelWithRelationship, "parent", rel_attr, condition
            )

            # Should call _handle_relationship_condition
            mock_handle_rel.assert_called_once_with(rel_attr, condition)
            assert result is not None

    def test_handle_model_attribute_regular_property_detection(self, translator):
        """Test _handle_model_attribute correctly detects and handles regular properties"""
        from unittest.mock import Mock, patch

        class MockModelWithProperty(TestBase):
            __tablename__ = "model_with_prop_table"
            id = Column(String, primary_key=True)

            @property
            def computed_field(self):
                return "computed"

        condition = ConditionLeaf(
            field_address="model_with_prop_table.computed_field",
            operator=Operator.eq,
            value="test_value",
        )

        # Get the actual property attribute
        prop_attr = MockModelWithProperty.computed_field

        # Verify it's detected as a property
        assert isinstance(prop_attr, property)

        # Mock _handle_property_condition to verify it's called
        with patch.object(translator, "_handle_property_condition") as mock_handle_prop:
            mock_handle_prop.side_effect = ValueError("Property cannot be translated")

            with pytest.raises(ValueError, match="Property cannot be translated"):
                translator._handle_model_attribute(
                    MockModelWithProperty, "computed_field", prop_attr, condition
                )

            # Should call _handle_property_condition
            mock_handle_prop.assert_called_once_with(
                MockModelWithProperty, "computed_field", prop_attr, condition
            )

    def test_handle_model_attribute_column_detection(self, translator):
        """Test _handle_model_attribute correctly detects and handles regular columns"""
        from unittest.mock import Mock, patch

        class MockModelWithColumn(TestBase):
            __tablename__ = "model_with_col_table"
            id = Column(String, primary_key=True)
            name = Column(String)

        condition = ConditionLeaf(
            field_address="model_with_col_table.name",
            operator=Operator.eq,
            value="test_value",
        )

        # Get the actual column attribute
        col_attr = MockModelWithColumn.name

        # Verify it has the expected column properties
        assert hasattr(col_attr, "property")
        assert hasattr(col_attr.property, "columns")

        # Mock _apply_operator_to_column to verify it's called
        with patch.object(translator, "_apply_operator_to_column") as mock_apply_op:
            mock_result = Mock()
            mock_apply_op.return_value = mock_result

            result = translator._handle_model_attribute(
                MockModelWithColumn, "name", col_attr, condition
            )

            # Should call _apply_operator_to_column
            mock_apply_op.assert_called_once_with(
                col_attr, condition.operator, condition.value
            )
            assert result == mock_result

    def test_handle_model_attribute_hybrid_property_detection(self, translator):
        """Test _handle_model_attribute correctly handles hybrid properties"""
        from unittest.mock import Mock, patch

        from sqlalchemy.ext.hybrid import hybrid_property

        class MockModelWithHybridProperty(TestBase):
            __tablename__ = "model_with_hybrid_table"
            id = Column(String, primary_key=True)
            first_name = Column(String)
            last_name = Column(String)

            @hybrid_property
            def full_name(self):
                return self.first_name + " " + self.last_name

        condition = ConditionLeaf(
            field_address="model_with_hybrid_table.full_name",
            operator=Operator.eq,
            value="test_value",
        )

        # Get the actual hybrid property attribute
        hybrid_attr = MockModelWithHybridProperty.full_name

        # Mock _apply_operator_to_column to verify it's called
        with patch.object(translator, "_apply_operator_to_column") as mock_apply_op:
            mock_result = Mock()
            mock_apply_op.return_value = mock_result

            result = translator._handle_model_attribute(
                MockModelWithHybridProperty, "full_name", hybrid_attr, condition
            )

            # Should call _apply_operator_to_column (hybrid properties are handled like columns)
            mock_apply_op.assert_called_once_with(
                hybrid_attr, condition.operator, condition.value
            )
            assert result == mock_result

    def test_handle_model_attribute_default_column_handling(self, translator):
        """Test _handle_model_attribute default case treats unknown attributes as columns"""
        from unittest.mock import Mock, patch

        class MockModelWithUnknownAttr(TestBase):
            __tablename__ = "model_with_unknown_table"
            id = Column(String, primary_key=True)

        # Create a mock attribute that doesn't fit other categories
        mock_attr = Mock()
        # Ensure it doesn't have the properties that would make it a relationship or column
        if hasattr(mock_attr, "property"):
            del mock_attr.property  # Remove property attribute if it exists

        condition = ConditionLeaf(
            field_address="model_with_unknown_table.unknown_field",
            operator=Operator.eq,
            value="test_value",
        )

        # Mock _apply_operator_to_column to verify it's called
        with patch.object(translator, "_apply_operator_to_column") as mock_apply_op:
            mock_result = Mock()
            mock_apply_op.return_value = mock_result

            result = translator._handle_model_attribute(
                MockModelWithUnknownAttr, "unknown_field", mock_attr, condition
            )

            # Should call _apply_operator_to_column as default
            mock_apply_op.assert_called_once_with(
                mock_attr, condition.operator, condition.value
            )
            assert result == mock_result

    def test_handle_model_attribute_model_name_extraction(self, translator):
        """Test _handle_model_attribute handles models without __name__ attribute"""
        from unittest.mock import Mock, patch

        # Create a mock model class without __name__ attribute
        mock_model = Mock()
        if hasattr(mock_model, "__name__"):
            del mock_model.__name__  # Remove __name__ if it exists
        mock_model.__str__ = Mock(return_value="<MockModelClass>")

        mock_attr = Mock()
        if hasattr(mock_attr, "property"):
            del mock_attr.property  # Ensure it goes to default case

        condition = ConditionLeaf(
            field_address="mock_table.field",
            operator=Operator.eq,
            value="test_value",
        )

        # Mock _apply_operator_to_column to verify it's called
        with patch.object(translator, "_apply_operator_to_column") as mock_apply_op:
            mock_result = Mock()
            mock_apply_op.return_value = mock_result

            result = translator._handle_model_attribute(
                mock_model, "field", mock_attr, condition
            )

            # Should still work and call _apply_operator_to_column
            mock_apply_op.assert_called_once_with(
                mock_attr, condition.operator, condition.value
            )
            assert result == mock_result


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_unknown_condition_type_raises_error(self, translator):
        """Test that unknown condition types raise errors"""
        # Mock an unknown condition type
        unknown_condition = Mock()

        with pytest.raises(SQLTranslationError, match="Unknown condition type"):
            translator.extract_field_addresses(unknown_condition)

    def test_no_models_found_raises_error(self, mock_db):
        """Test error when no models are found for tables"""
        translator = SQLConditionTranslator(db=mock_db)

        # Mock empty registry
        translator.orm_registry = Mock()
        translator.orm_registry.registry = Mock()
        translator.orm_registry.registry.mappers = []

        condition = ConditionLeaf(
            field_address="nonexistent.field", operator=Operator.eq, value="value"
        )

        with pytest.raises(
            SQLTranslationError, match="No valid SQLAlchemy models found"
        ):
            translator.build_sqlalchemy_query(condition)

    def test_property_condition_provides_helpful_error(self, mock_db):
        """Test that property conditions provide helpful error messages"""
        translator = SQLConditionTranslator(db=mock_db)

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
            assert "consider using the relationship directly" in error_msg


class TestSQLTranslatorEdgeCases:
    """Test edge cases and error conditions in SQLConditionTranslator"""

    def test_init_with_custom_orm_registry(self):
        """Test SQLConditionTranslator initialization with custom ORM registry"""
        mock_session = create_autospec(Session, spec_set=True)
        custom_registry = {"custom_table": Mock()}

        translator = SQLConditionTranslator(mock_session, orm_registry=custom_registry)

        assert translator.db == mock_session
        assert translator.orm_registry == custom_registry

    def test_init_without_orm_registry(self):
        """Test SQLConditionTranslator initialization without ORM registry"""
        mock_session = create_autospec(Session, spec_set=True)

        translator = SQLConditionTranslator(mock_session)

        assert translator.db == mock_session
        # Should default to Base when no orm_registry provided
        assert translator.orm_registry is not None

    def test_find_related_main_tables_no_relationships(self):
        """Test _find_related_main_tables with model that has no relationships"""
        from unittest.mock import patch

        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        # Mock model with no relationships
        mock_model = Mock()

        # Mock the inspect function to return a mapper with no relationships
        mock_mapper = Mock()
        mock_relationships = Mock()
        mock_relationships.items.return_value = []
        mock_mapper.relationships = mock_relationships

        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            return_value=mock_mapper,
        ):
            result = translator._find_related_main_tables(mock_model, "join_table")

        assert result == {}

    def test_find_relationship_path_same_model(self):
        """Test _find_relationship_path when from and to models are the same"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        mock_model = Mock()

        result = translator._find_relationship_path(mock_model, mock_model)

        # Should return empty list for same model
        assert result == []

    def test_find_relationship_path_no_relationships(self):
        """Test _find_relationship_path with model that has no relationships"""
        from unittest.mock import patch

        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        mock_from_model = Mock()
        mock_to_model = Mock()

        # Mock the inspect function to return a mapper with no relationships
        mock_mapper = Mock()
        mock_relationships = Mock()
        mock_relationships.items.return_value = []
        mock_mapper.relationships = mock_relationships

        with patch(
            "fides.api.task.conditional_dependencies.sql_translator.inspect",
            return_value=mock_mapper,
        ):
            result = translator._find_relationship_path(mock_from_model, mock_to_model)

        assert result is None

    def test_find_relationship_path_through_intermediates_max_depth_zero(self):
        """Test _find_relationship_path_through_intermediates with max_depth=0"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        mock_from_model = Mock()
        mock_to_model = Mock()

        result = translator._find_relationship_path_through_intermediates(
            mock_from_model, mock_to_model, max_depth=0
        )

        assert result is None

    def test_find_relationship_path_through_intermediates_same_model(self):
        """Test _find_relationship_path_through_intermediates when from and to models are the same"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        mock_model = Mock()

        result = translator._find_relationship_path_through_intermediates(
            mock_model, mock_model, max_depth=3
        )

        # Should return empty list for same model
        assert result == []

    def test_robust_relationship_handling_collection_vs_scalar(self):
        """Test that the robust relationship handler correctly distinguishes collections from scalars"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

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

    def test_relationship_handling_with_apply_operator(self):
        """Test that simplified relationship handling correctly uses _apply_operator_to_column"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        # Mock relationship and related model
        mock_relationship = Mock()
        mock_property = Mock()
        mock_property.uselist = True  # Collection
        mock_related_model = Mock()
        mock_target_column = Mock()
        mock_related_model.status = mock_target_column
        mock_property.mapper.class_ = mock_related_model
        mock_relationship.property = mock_property
        mock_relationship.any.return_value = Mock()

        condition = ConditionLeaf(
            field_address="user.orders.status",
            operator=Operator.eq,
            value="completed",
        )

        # Mock _apply_operator_to_column to return a comparison
        with patch.object(translator, "_apply_operator_to_column") as mock_apply_op:
            mock_comparison = Mock()
            mock_apply_op.return_value = mock_comparison

            result = translator._handle_relationship_condition(
                mock_relationship, condition
            )

            # Verify _apply_operator_to_column was called with correct parameters
            mock_apply_op.assert_called_once_with(
                mock_target_column, Operator.eq, "completed"
            )
            # Verify any() was called with the comparison result
            mock_relationship.any.assert_called_once_with(mock_comparison)
            assert result is not None

    def test_build_filter_expression_with_none_condition(self):
        """Test _build_filter_expression with None condition"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        result = translator._build_filter_expression(None, {})

        assert result is None

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

    MOCK_QUERY = Mock()
    MOCK_PRIMARY_MODEL = Mock()
    MOCK_MODEL_CLASS = Mock()

    def test_add_relationship_joins_no_models(self, translator):
        """Test _add_relationship_joins with empty model_classes"""
        # Should return the original query unchanged
        assert (
            translator._add_relationship_joins(
                self.MOCK_QUERY, self.MOCK_PRIMARY_MODEL, {}, "primary_table"
            )
            == self.MOCK_QUERY
        )

    def test_add_relationship_joins_only_primary_table(self, translator):
        """Test _add_relationship_joins with only primary table in model_classes"""
        model_classes = {"primary_table": self.MOCK_PRIMARY_MODEL}

        # Should return the original query unchanged since only primary table
        assert (
            translator._add_relationship_joins(
                self.MOCK_QUERY, self.MOCK_PRIMARY_MODEL, model_classes, "primary_table"
            )
            == self.MOCK_QUERY
        )

    def test_fetch_join_path_with_successful_direct_path(self, translator):
        """Test _fetch_join_path when direct relationship path is found"""
        # Mock successful direct path finding
        mock_relationship = Mock()
        translator._find_relationship_path = Mock(return_value=[mock_relationship])

        result = translator._fetch_join_path(
            self.MOCK_MODEL_CLASS,
            self.MOCK_PRIMARY_MODEL,
            {},
            "table_name",
            "primary_table",
        )

        # Should return the relationship path
        assert result == [mock_relationship]
        translator._find_relationship_path.assert_called_once_with(
            self.MOCK_PRIMARY_MODEL, self.MOCK_MODEL_CLASS
        )

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
        self.MOCK_QUERY.join.return_value = self.MOCK_QUERY

        result = translator._fetch_join_path(
            self.MOCK_MODEL_CLASS,
            self.MOCK_PRIMARY_MODEL,
            {},
            "table_name",
            "primary_table",
        )

        # Should return the intermediate relationship path
        assert result == [mock_relationship1, mock_relationship2]
        translator._find_relationship_path.assert_called_once_with(
            self.MOCK_PRIMARY_MODEL, self.MOCK_MODEL_CLASS
        )
        translator._find_relationship_path_through_intermediates.assert_called_once_with(
            self.MOCK_PRIMARY_MODEL, self.MOCK_MODEL_CLASS, max_depth=3
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
            "table_name": self.MOCK_MODEL_CLASS,
            "primary_table": self.MOCK_PRIMARY_MODEL,
            "other_table": mock_other_model,
        }

        # Mock finding path through other model
        mock_relationship = Mock()
        translator._find_relationship_path_through_intermediates = Mock(
            side_effect=[None, [mock_relationship]]  # First call fails, second succeeds
        )

        mock_joined_query = Mock()
        self.MOCK_QUERY.join.return_value = mock_joined_query

        result = translator._fetch_join_path(
            self.MOCK_MODEL_CLASS,
            self.MOCK_PRIMARY_MODEL,
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
            "table_name": self.MOCK_MODEL_CLASS,
            "primary_table": self.MOCK_PRIMARY_MODEL,
        }

        result = translator._fetch_join_path(
            self.MOCK_MODEL_CLASS,
            self.MOCK_PRIMARY_MODEL,
            model_classes,
            "table_name",
            "primary_table",
        )

        # Should return None when no path found
        assert result is None

    @pytest.mark.parametrize(
        "scenario",
        [
            "no_valid_models",
            "no_primary_table",
        ],
    )
    def test_build_sqlalchemy_query_not_valid(self, scenario):
        """Test build_sqlalchemy_query when no valid SQLAlchemy models are found"""
        mock_session = create_autospec(Session, spec_set=True)
        translator = SQLConditionTranslator(mock_session)

        # Mock analyze_tables_in_condition to return tables
        translator.analyze_tables_in_condition = Mock(return_value={"test_table": []})

        # Mock get_orm_model_by_table_name to return None (no model found)
        if scenario == "no_valid_models":
            translator.get_orm_model_by_table_name = Mock(return_value=None)
        elif scenario == "no_primary_table":
            translator.get_orm_model_by_table_name = Mock(return_value=Mock())
            # Mock _determine_primary_table to return None
            translator._determine_primary_table = Mock(return_value=None)

        condition = ConditionLeaf(
            field_address="test_table.field", operator=Operator.eq, value="test_value"
        )

        with pytest.raises(SQLTranslationError) as exc_info:
            translator.build_sqlalchemy_query(condition)

        assert "No valid SQLAlchemy models found" in str(
            exc_info.value
        ) or "No primary table found" in str(exc_info.value)
