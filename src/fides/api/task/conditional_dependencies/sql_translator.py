from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Query, RelationshipProperty, Session

from fides.api.db.base_class import Base
from fides.api.task.conditional_dependencies.schemas import (
    Condition,
    ConditionGroup,
    ConditionLeaf,
    GroupOperator,
    Operator,
)
from fides.api.task.conditional_dependencies.sql_schemas import (
    OPERATOR_MAP,
    FieldAddress,
    SQLTranslationError,
)


class SQLConditionTranslator:
    """Translates conditional dependencies into SQLAlchemy queries using relationship traversal"""

    def __init__(self, db: Session, orm_registry=None):
        """
        Initialize the SQL translator using SQLAlchemy's relationship traversal

        This translator leverages SQLAlchemy's built-in relationship handling for:
        - Automatic JOIN optimization
        - Type-safe column references
        - Built-in query caching
        - Clean relationship traversal

        Args:
            db: SQLAlchemy database session for query execution
            orm_registry: Optional SQLAlchemy registry or Base class for ORM introspection
        """
        self.db = db
        self.orm_registry = orm_registry or Base
        self._model_cache = {}

    def extract_field_addresses(self, condition: Condition) -> set[FieldAddress]:
        """
        Extract all field addresses from a condition tree

        Args:
            condition: The condition to analyze

        Returns:
            Set of FieldAddress objects
        """
        field_addresses = set()

        if isinstance(condition, ConditionLeaf):
            field_addr = FieldAddress.parse(condition.field_address)
            field_addresses.add(field_addr)
            return field_addresses

        if isinstance(condition, ConditionGroup):
            for sub_condition in condition.conditions:
                field_addresses.update(self.extract_field_addresses(sub_condition))
            return field_addresses

        raise SQLTranslationError(f"Unknown condition type: {type(condition)}")

    def analyze_tables_in_condition(
        self, condition: Condition
    ) -> dict[str, list[FieldAddress]]:
        """
        Analyze which tables are referenced in a condition and group field addresses by table

        Args:
            condition: The condition to analyze

        Returns:
            Dictionary mapping table names to lists of field addresses for that table
        """
        field_addresses = self.extract_field_addresses(condition)

        # Group field addresses by table
        tables_to_fields = {}
        for field_addr in field_addresses:
            if not field_addr.table_name:
                raise SQLTranslationError(
                    f"Table name not specified for field address: {field_addr.full_address}"
                )

            if field_addr.table_name not in tables_to_fields:
                tables_to_fields[field_addr.table_name] = []
            tables_to_fields[field_addr.table_name].append(field_addr)

        return tables_to_fields

    def get_orm_model_by_table_name(self, table_name: str):
        """
        Find the ORM model class for a given table name (with caching)

        Uses the Base class's subclasses to find models - much simpler and cleaner
        than accessing SQLAlchemy internals.

        Args:
            table_name: Database table name

        Returns:
            SQLAlchemy model class or None if not found
        """
        # Check cache first
        if table_name in self._model_cache:
            return self._model_cache[table_name]

        # Only try to get subclasses if orm_registry is a real class (not a mock)
        if hasattr(self.orm_registry, "__subclasses__"):
            try:
                # Search through all subclasses of the Base class
                for subclass in self._get_all_subclasses(self.orm_registry):
                    if (
                        hasattr(subclass, "__tablename__")
                        and subclass.__tablename__ == table_name
                    ):
                        self._model_cache[table_name] = subclass
                        return subclass
            except (AttributeError, TypeError):
                # Handle cases where orm_registry is a mock or doesn't support subclasses
                pass

        # If not found or can't access subclasses, cache None and return
        self._model_cache[table_name] = None
        return None

    def _get_all_subclasses(self, cls):
        """
        Recursively get all subclasses of a class

        Args:
            cls: The base class

        Returns:
            Set of all subclasses
        """
        subclasses = set(cls.__subclasses__())
        for subclass in list(subclasses):
            subclasses.update(self._get_all_subclasses(subclass))
        return subclasses

    def build_sqlalchemy_query(self, condition: Condition) -> Query:
        """
        Build SQLAlchemy Query object using relationship traversal

        This leverages SQLAlchemy's built-in relationship handling instead of manual JOIN discovery.
        Benefits:
        - Automatic JOIN optimization
        - Uses existing relationship() definitions
        - Type safety and IDE support
        - Handles complex relationship patterns

        Args:
            condition: The condition to translate into a Query

        Returns:
            SQLAlchemy Query object

        Raises:
            SQLTranslationError: If db is not provided or models not found
        """
        # Analyze which tables/models are needed
        tables_to_fields = self.analyze_tables_in_condition(condition)
        model_classes = {}

        for table_name in tables_to_fields.keys():
            model_class = self.get_orm_model_by_table_name(table_name)
            if model_class:
                model_classes[table_name] = model_class

        if not model_classes:
            raise SQLTranslationError(
                "No valid SQLAlchemy models found for the specified tables"
            )

        # Determine primary model (most connected or first alphabetically)
        primary_table = self._determine_primary_table(model_classes, tables_to_fields)
        primary_model = model_classes[primary_table]

        # Build base query - select all fields mentioned in conditions
        select_fields = self._build_select_fields(tables_to_fields, model_classes)
        query = self.db.query(*select_fields)

        # Add JOINs using relationships
        query = self._add_relationship_joins(
            query, primary_model, model_classes, primary_table
        )

        # Add WHERE conditions
        query = self._add_condition_filters(query, condition, model_classes)

        return query

    def _determine_primary_table(
        self,
        model_classes: dict[str, type],
        tables_to_fields: dict[str, list[FieldAddress]],
    ) -> str:
        """Determine which model should be the primary query target"""
        # Strategy: Use the table with the most fields in conditions, or first alphabetically
        max_fields = 0
        primary_table = None

        for table_name, fields in tables_to_fields.items():
            if table_name in model_classes and len(fields) > max_fields:
                max_fields = len(fields)
                primary_table = table_name

        return primary_table or sorted(model_classes.keys())[0]

    def _build_select_fields(
        self,
        tables_to_fields: dict[str, list[FieldAddress]],
        model_classes: dict[str, type],
    ) -> list:
        """Build list of fields to select in the query"""
        select_fields = []

        for table_name, field_addresses in tables_to_fields.items():
            if table_name not in model_classes:
                continue

            model_class = model_classes[table_name]

            for field_addr in field_addresses:
                if hasattr(model_class, field_addr.base_field_name):
                    column = getattr(model_class, field_addr.base_field_name)
                    select_fields.append(column)

        return select_fields or [
            list(model_classes.values())[0]
        ]  # Fallback to first model

    def _add_relationship_joins(
        self,
        query: Query,
        primary_model: type,
        model_classes: dict[str, type],
        primary_table: str,
    ) -> Query:
        """
        Add JOINs using SQLAlchemy relationships

        This is where SQLAlchemy shines - it automatically determines JOIN conditions
        """
        for table_name, model_class in model_classes.items():
            if table_name == primary_table:
                continue

            # Try to find relationship path from primary to this model
            join_path = self._find_relationship_path(primary_model, model_class)

            if join_path:
                # Apply JOINs using the relationship path
                for relationship_attr in join_path:
                    query = query.join(relationship_attr)
            else:
                # Try to find any model that can reach this one
                joined = False
                for joined_table, joined_model in model_classes.items():
                    if joined_table == table_name or joined_table == primary_table:
                        continue

                    path = self._find_relationship_path(joined_model, model_class)
                    if path:
                        for relationship_attr in path:
                            query = query.join(relationship_attr)
                        joined = True
                        break

                if not joined:
                    # Log warning but don't fail - the query might still work
                    pass

        return query

    def _find_relationship_path(
        self, from_model: type, to_model: type
    ) -> Optional[list]:
        """
        Find relationship path between two models using SQLAlchemy introspection

        This uses the relationship() definitions in the models to find traversal paths
        """
        if from_model == to_model:
            return []

        # Get mapper for the source model
        mapper = inspect(from_model)

        # Check direct relationships
        for relationship_name, relationship_prop in mapper.relationships.items():
            if isinstance(relationship_prop, RelationshipProperty):
                target_mapper = relationship_prop.mapper
                if target_mapper.class_ == to_model:
                    # Direct relationship found
                    return [getattr(from_model, relationship_name)]

        # For now, only handle direct relationships
        # Could be enhanced to handle multi-hop relationships
        return None

    def _add_condition_filters(
        self, query: Query, condition: Condition, model_classes: dict[str, type]
    ) -> Query:
        """Add WHERE conditions to the SQLAlchemy query"""
        filter_expression = self._build_filter_expression(condition, model_classes)
        if filter_expression is not None:
            query = query.filter(filter_expression)
        return query

    def _build_filter_expression(
        self, condition: Condition, model_classes: dict[str, type]
    ):
        """Build SQLAlchemy filter expressions from conditions"""
        if isinstance(condition, ConditionLeaf):
            return self._build_leaf_filter(condition, model_classes)
        if isinstance(condition, ConditionGroup):
            sub_filters = []
            for sub_cond in condition.conditions:
                sub_filter = self._build_filter_expression(sub_cond, model_classes)
                if sub_filter is not None:
                    sub_filters.append(sub_filter)

            if not sub_filters:
                return None

            if condition.logical_operator == GroupOperator.and_:
                return and_(*sub_filters)
            if condition.logical_operator == GroupOperator.or_:
                return or_(*sub_filters)

        return None

    def _build_leaf_filter(
        self, condition: ConditionLeaf, model_classes: dict[str, type]
    ):
        """Build filter expression for a single condition using SQLAlchemy column objects"""
        field_addr = FieldAddress.parse(condition.field_address)

        if not field_addr.table_name or field_addr.table_name not in model_classes:
            return None

        model_class = model_classes[field_addr.table_name]

        # Handle JSON path fields
        if field_addr.json_path:
            if hasattr(model_class, field_addr.base_field_name):
                column = getattr(model_class, field_addr.base_field_name)
                # Use PostgreSQL JSON operators
                json_expr = column[field_addr.json_path].astext
                return self._apply_operator_to_column(
                    json_expr, condition.operator, condition.value
                )
        else:
            # Regular column
            if hasattr(model_class, field_addr.base_field_name):
                column = getattr(model_class, field_addr.base_field_name)
                return self._apply_operator_to_column(
                    column, condition.operator, condition.value
                )

        return None

    def _apply_operator_to_column(self, column, operator: Operator, value):
        """Apply the specified operator to a SQLAlchemy column"""
        # Map operators to their corresponding SQLAlchemy expressions

        if operator in OPERATOR_MAP:
            return OPERATOR_MAP[operator](column, value)
        # Add more operators as needed
        raise SQLTranslationError(
            f"Unsupported operator for SQLAlchemy query: {operator}"
        )

    def generate_query_from_condition(
        self,
        condition: Condition,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Query:
        """
        Generate SQLAlchemy Query from conditions

        Args:
            condition: The condition to translate
            limit: Optional LIMIT clause
            offset: Optional OFFSET clause

        Returns:
            SQLAlchemy Query object
        """
        query = self.build_sqlalchemy_query(condition)

        if limit is not None:
            query = query.limit(limit)

        if offset is not None:
            query = query.offset(offset)

        return query

    def generate_count_query(self, condition: Condition) -> Query:
        """
        Generate a COUNT query from conditions

        Args:
            condition: The condition to translate

        Returns:
            SQLAlchemy Query object for counting
        """
        # Analyze tables in the condition
        tables_to_fields = self.analyze_tables_in_condition(condition)
        model_classes = {}

        for table_name in tables_to_fields.keys():
            model_class = self.get_orm_model_by_table_name(table_name)
            if model_class:
                model_classes[table_name] = model_class

        if not model_classes:
            raise SQLTranslationError(
                "No valid SQLAlchemy models found for the specified tables"
            )

        # Use the primary model for COUNT
        primary_table = self._determine_primary_table(model_classes, tables_to_fields)
        primary_model = model_classes[primary_table]

        # Build COUNT query
        query = self.db.query(primary_model).filter(
            self._build_filter_expression(condition, model_classes)
        )

        return query.count()
