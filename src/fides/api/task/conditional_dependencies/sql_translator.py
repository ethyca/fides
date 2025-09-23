from collections import deque
from typing import Any, Optional

from loguru import logger
from sqlalchemy import and_, not_, or_
from sqlalchemy.exc import NoInspectionAvailable
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

    MAX_RELATIONSHIP_DEPTH = 15
    DEFAULT_PRIMARY_KEY = "id"

    def __init__(self, db: Session, orm_registry: Optional[Base] = None):
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
        self.db: Session = db
        self.orm_registry: Any = orm_registry if orm_registry else Base
        self._model_cache: dict[str, Optional[type]] = (
            self._build_table_to_model_mapping()
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

    def build_sqlalchemy_query(self, condition: Condition) -> Query:
        """Builds SQLAlchemy Query object using relationship traversal

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
        tables_to_fields = self.map_tables_to_fields(condition)
        model_classes: dict[str, type] = {
            table_name: model_class
            for table_name in tables_to_fields
            if (model_class := self._model_cache.get(table_name)) is not None
        }

        if not model_classes:
            raise SQLTranslationError(
                "No valid SQLAlchemy models found for the specified tables"
            )

        # Determine primary model - first table in the model_classes dictionary (first condition)
        # This makes the query intent clear and predictable for users
        primary_table, primary_model = next(iter(model_classes.items()))

        # If there are multiple tables, expand the model classes to include related main tables
        # This is necessary for join/reference tables
        if len(model_classes) > 1:
            # For join/reference tables, try to find their related main tables
            expanded_model_classes = self._expand_with_related_main_tables(
                model_classes, tables_to_fields
            )
            for table_name, model_class in expanded_model_classes.items():
                if table_name not in model_classes:
                    model_classes[table_name] = model_class
                    tables_to_fields[table_name] = []

        # Build base query - select from primary model (equivalent to SELECT *)
        query: Query = self.db.query(primary_model)

        # Add JOINs using relationships
        query = self._add_relationship_joins(
            query, primary_model, model_classes, primary_table, tables_to_fields
        )

        # Add WHERE conditions
        filter_expression = self._build_filter_expression(condition, model_classes)
        if filter_expression is not None:
            query = query.filter(filter_expression)

        return query

    def map_tables_to_fields(
        self, condition: Condition
    ) -> dict[str, list[FieldAddress]]:
        """Maps field addresses by table which are referenced in a condition

        Args:
            condition: The condition to analyze

        Returns:
            Dictionary mapping table names to lists of field addresses for that table
            (preserves order of first appearance)
        """
        field_addresses = self.extract_field_addresses(condition)

        # Group field addresses by table, preserving order of first appearance
        tables_to_fields: dict[str, list[FieldAddress]] = {}
        for field_addr in field_addresses:
            if not field_addr.table_name:
                raise SQLTranslationError(
                    f"Table name not specified for field address: {field_addr.full_address}"
                )

            if field_addr.table_name not in tables_to_fields:
                tables_to_fields[field_addr.table_name] = []
            tables_to_fields[field_addr.table_name].append(field_addr)

        return tables_to_fields

    def extract_field_addresses(self, condition: Condition) -> list[FieldAddress]:
        """Extracts all field addresses from a condition tree in order.
        The order is important for determining the primary table.

        Args:
            condition: The condition to analyze

        Returns:
            List of FieldAddress objects in the order they appear
        """
        field_addresses = []

        if isinstance(condition, ConditionLeaf):
            field_addr = FieldAddress.parse(condition.field_address)
            field_addresses.append(field_addr)
            return field_addresses

        if isinstance(condition, ConditionGroup):
            for sub_condition in condition.conditions:
                field_addresses.extend(self.extract_field_addresses(sub_condition))
            return field_addresses

        raise SQLTranslationError(f"Unknown condition type: {type(condition)}")

    def _build_table_to_model_mapping(self) -> dict[str, Optional[type]]:
        """Build complete table name to model mapping once"""
        mapping = {}
        for mapper in self.orm_registry.registry.mappers:
            table_name = getattr(mapper.class_, "__tablename__", None)
            if table_name:
                mapping[table_name] = mapper.class_
        return mapping

    def _apply_operator_to_column(
        self, column: Any, operator: Operator, value: Any
    ) -> Any:
        """Apply the specified operator to a SQLAlchemy column"""
        if operator in OPERATOR_MAP:
            return OPERATOR_MAP[operator](column, value)
        raise SQLTranslationError(
            f"Unsupported operator for SQLAlchemy query: {operator}"
        )

    def _expand_with_related_main_tables(
        self, model_classes: dict[str, type], tables_to_fields: dict[str, list]
    ) -> dict[str, type]:
        """Finds and includes related tables for join/reference tables

        This helps with relationship queries where conditions are on join tables
        but we want to return records from the main entities.

        Args:
            model_classes: Dictionary of table names to model classes
            tables_to_fields: Dictionary of table names to lists of field addresses

        Returns:
            Dictionary of table names to model classes
        """
        expanded_model_classes = {}

        for table_name, model_class in model_classes.items():
            # Check if it has relationships (indicating it might be a join table)
            try:
                mapper = inspect(model_class)
            except NoInspectionAvailable:
                continue
            has_relationships = len(mapper.relationships) > 0

            # Consider it a potential join table if it matches name patterns OR has relationships
            if has_relationships:
                # Try to find related main tables through relationships
                main_tables = self._find_related_main_tables(model_class, table_name)
                for main_table_name, main_model_class in main_tables.items():
                    if main_table_name not in expanded_model_classes:
                        expanded_model_classes[main_table_name] = main_model_class

        return expanded_model_classes

    def _find_related_main_tables(
        self, join_model_class: type, join_table_name: str
    ) -> dict[str, type]:
        """Finds main tables that have relationships to this join table

        For example, if we have ManualTaskReference, find ManualTask

        Args:
            join_model_class: The model class of the join table
            join_table_name: The name of the join table

        Returns:
            Dictionary of table names to model classes
        """
        related_tables = {}
        try:
            mapper = inspect(join_model_class)
        except NoInspectionAvailable:
            return {}

        # Look at relationships from the join table to related tables
        for _, relationship_prop in mapper.relationships.items():
            if hasattr(relationship_prop, "mapper"):
                target_model = relationship_prop.mapper.class_
                target_table_name = getattr(target_model, "__tablename__", None)

                if target_table_name and target_table_name != join_table_name:
                    related_tables[target_table_name] = target_model

        return related_tables

    def _find_relationship_path_through_intermediates(
        self, from_model: type, to_model: type, max_depth: Optional[int] = None
    ) -> list:
        """Finds a relationship path between models, including through intermediate tables

        Uses breadth-first search to find the shortest path through relationships.
        This can discover paths like: ManualTask -> ManualTaskReference -> FidesUser

        Args:
            from_model: Source model class
            to_model: Target model class
            max_depth: Maximum relationship hops to explore

        Returns:
            List of relationship attributes to traverse, or empty list if no path found
        """
        if from_model == to_model:
            return []

        # Use the class constant if no max_depth provided
        if max_depth is None:
            max_depth = self.MAX_RELATIONSHIP_DEPTH

        # Use BFS to find shortest relationship path
        # Queue items: (current_model, path_so_far)
        queue: deque[tuple[type, list]] = deque([(from_model, [])])
        visited: set[type] = {from_model}

        for _ in range(max_depth):
            if not queue:
                break

            for _ in range(len(queue)):
                current_model, current_path = queue.popleft()

                try:
                    mapper = inspect(current_model)
                except NoInspectionAvailable:
                    continue

                # Explore all relationships from current model
                for (
                    relationship_name,
                    relationship_prop,
                ) in mapper.relationships.items():
                    if hasattr(relationship_prop, "mapper"):
                        next_model = relationship_prop.mapper.class_
                        logger.info(
                            f"Found relationship: {relationship_name} from {current_model.__name__} to {next_model.__name__}"
                        )

                        # Found target model
                        if next_model == to_model:
                            logger.info(f"Found target model: {next_model.__name__}")
                            return current_path + [
                                getattr(current_model, relationship_name)
                            ]

                        # Add to queue for further exploration if not visited
                        if next_model not in visited:
                            logger.info(f"Adding to queue: {next_model.__name__}")
                            visited.add(next_model)
                            current = current_path + [
                                getattr(current_model, relationship_name)
                            ]
                            queue.append((next_model, current))
        return []

    def _fetch_join_path(
        self,
        model_class: type,
        primary_model: type,
        model_classes: dict[str, type],
        table_name: str,
        primary_table: str,
    ) -> list:
        """Fetch the join path for the given model class
        This will attempt to find a relationship path between the primary model and the given model class.
        If no path is found, it will return None.

        Args:
            model_class: The model class to find the join path for
            primary_model: The primary model class
            model_classes: Dictionary of table names to model classes
            table_name: The table name for the model class
            primary_table: The primary table name

        Returns:
            The list of relationship attributes to join, or empty list if no path found
        """
        # Try to find direct relationship path first
        join_path = self._find_relationship_path(primary_model, model_class)
        if join_path:
            logger.debug(
                f"Found direct relationship path from {primary_model.__name__} to {model_class.__name__}: {[str(attr) for attr in join_path]}"
            )
            return join_path

        # Try to find path through intermediate tables
        join_path = self._find_relationship_path_through_intermediates(
            primary_model, model_class
        )
        if join_path:
            logger.debug(
                f"Found intermediate relationship path from {primary_model.__name__} to {model_class.__name__}: {[str(attr) for attr in join_path]}"
            )
            return join_path

        # Try to find any model that can reach this one (fallback)
        for joined_table, joined_model in model_classes.items():
            if joined_table in [table_name, primary_table]:
                continue

            join_path = self._find_relationship_path_through_intermediates(
                joined_model, model_class
            )
            if join_path:
                return join_path

        return []

    def _add_relationship_joins(
        self,
        query: Query,
        primary_model: type,
        model_classes: dict[str, type],
        primary_table: str,
        tables_to_fields: dict[str, list],
    ) -> Query:
        """Adds JOINs using SQLAlchemy relationships

        Args:
            query: The SQLAlchemy query to add the JOINs to
            primary_model: The primary model class
            model_classes: Dictionary of table names to model classes
            primary_table: The primary table name
            tables_to_fields: Dictionary of table names to lists of field addresses

        Returns:
            The SQLAlchemy query with the JOINs added or the original query if no join paths found
        """
        for table_name, model_class in model_classes.items():
            if table_name == primary_table:
                continue
            # Only join tables that have actual field references (conditions)
            # Skip auto-discovered related tables that aren't referenced in conditions
            if table_name not in tables_to_fields or not tables_to_fields[table_name]:
                continue
            join_path = self._fetch_join_path(
                model_class,
                primary_model,
                model_classes,
                table_name,
                primary_table,
            )
            if join_path:
                for relationship_attr in join_path:
                    # Check if this is a reverse relationship (target model has relationship to primary model)
                    if (
                        hasattr(relationship_attr, "property")
                        and hasattr(relationship_attr.property, "mapper")
                        and relationship_attr.property.mapper.class_ == primary_model
                    ):
                        query = self._apply_reverse_join(
                            query, relationship_attr, primary_model
                        )
                    else:
                        query = query.join(relationship_attr)
        return query

    def _apply_reverse_join(
        self, query: Query, relationship_attr: Any, primary_model: Any
    ) -> Query:
        """Applies a reverse join to the query
        For reverse relationships, we need to join using the relationship but in reverse
        The relationship contains the correct primaryjoin condition

        Args:
            query: The SQLAlchemy query to add the JOINs to
            relationship_attr: The relationship attribute to join
            primary_model: The primary model class

        Returns:
            The SQLAlchemy query with the JOINs added or the original query if no join paths found
        """
        logger.debug(
            f"Reverse relationship detected: {relationship_attr} points back to primary table {primary_model.__name__}"
        )
        target_model = relationship_attr.class_
        if (
            hasattr(relationship_attr.property, "primaryjoin")
            and relationship_attr.property.primaryjoin is not None
        ):
            join_condition = relationship_attr.property.primaryjoin
            query = query.join(target_model, join_condition)
        else:
            raise SQLTranslationError(
                f"No primaryjoin found for {primary_model.__name__}, {target_model.__name__}"
            )
        return query

    def _find_relationship_path(self, from_model: type, to_model: type) -> list:
        """Finds relationship path between two models using SQLAlchemy introspection

        This uses the relationship() definitions in the models to find traversal paths.
        This function only finds direct relationships. Multi-hop relationships are handled by
        _find_relationship_path_through_intermediates.

        Args:
            from_model: The source model class
            to_model: The target model class

        Returns:
            The list of relationship attributes to join, or empty list if no path found
        """
        join_path: dict[type, list[Any]] = {}
        if from_model == to_model:
            return []

        logger.debug(
            f"Looking for relationship path from {from_model.__name__} to {to_model.__name__}"
        )

        # Get mapper for the source model
        try:
            mapper = inspect(from_model)
            target_mapper = inspect(to_model)
        except NoInspectionAvailable:
            logger.debug(
                f"Could not inspect models {from_model.__name__} or {to_model.__name__}"
            )
            return []
        # Check direct relationships bi-directional
        for m, t in [(mapper, to_model), (target_mapper, from_model)]:
            join_path[m.class_] = []

            for relationship_name, relationship_prop in m.relationships.items():
                if isinstance(relationship_prop, RelationshipProperty):
                    relationship_target_mapper = relationship_prop.mapper
                    if relationship_target_mapper.class_ == t:
                        # Direct relationship found
                        join_path[m.class_].append(getattr(m.class_, relationship_name))

        # Return non-empty path if it exists
        from_model_path = join_path[mapper.class_]
        to_model_path = join_path[target_mapper.class_]

        # Prefer forward relationships (from source to target) over reverse relationships
        if len(from_model_path) > 0:
            return from_model_path
        return to_model_path

    def _build_filter_expression(
        self, condition: Condition, model_classes: dict[str, type]
    ) -> Optional[Any]:
        """Builds SQLAlchemy filter expressions from conditions

        Args:
            condition: The condition to build the filter expression for
            model_classes: Dictionary of table names to model classes

        Returns:
            The SQLAlchemy filter expression, or None if no filter expression can be built
        """
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
    ) -> Optional[Any]:
        """Builds filter expression for a single condition using SQLAlchemy column objects

        Args:
            condition: The condition to build the filter expression for
            model_classes: Dictionary of table names to model classes

        Returns:
            The SQLAlchemy filter expression, or None if no filter expression can be built
        """
        field_addr = FieldAddress.parse(condition.field_address)

        if not field_addr.table_name or field_addr.table_name not in model_classes:
            raise SQLTranslationError(
                f"Table {field_addr.table_name} not found in model_classes"
            )

        model_class = model_classes[field_addr.table_name]
        field_name = field_addr.column_name
        # Always check if the column exists first
        if hasattr(model_class, field_addr.column_name):
            attr = getattr(model_class, field_addr.column_name)

            # Check if it's a relationship first
            # This handles cases like "fidesuser.permissions.role" where permissions is a relationship
            if hasattr(attr, "property") and isinstance(
                attr.property, RelationshipProperty
            ):
                return self._handle_relationship_condition(attr, condition)

            # Check if it's a regular property
            if isinstance(attr, property):
                # Try to find a SQL equivalent for the property - This currently raises an error.
                return self._handle_property_condition(
                    model_class, field_name, attr, condition
                )

            if field_addr.json_path is not None and len(field_addr.json_path) > 0:
                # Build JSON path expression safely using SQLAlchemy's chained [] operators
                json_path_components = field_addr.json_path
                for (
                    path_component
                ) in json_path_components:  # pylint: disable=not-an-iterable
                    attr = attr[path_component]
                attr = attr.astext
                return self._apply_operator_to_column(
                    attr, condition.operator, condition.value
                )
            return self._apply_operator_to_column(
                attr, condition.operator, condition.value
            )
        raise SQLTranslationError(
            f"Column {field_addr.column_name} not found on model {model_class.__name__}"
        )

    def _handle_relationship_condition(
        self, relationship_attr: Any, condition: ConditionLeaf
    ) -> Optional[Any]:
        """Handles conditions on relationships using SQLAlchemy's any() and has() methods

        This method leverages existing operator handling by:
        1. Extracting the target field from field_address or using primary key
        2. Getting the target column from the related model
        3. Using _apply_operator_to_column for consistent operator handling
        4. Wrapping the result in any() or has() based on relationship type

        Args:
            relationship_attr: SQLAlchemy relationship attribute
            condition: The condition being applied (field_address should be 'table.relationship.field')

        Returns:
            SQLAlchemy expression using any() or has(), or None if unsupported
        """
        field_address = FieldAddress.parse(condition.field_address)
        target_field = self._extract_relationship_target_field(
            field_address, relationship_attr
        )

        # Get relationship property for inspection
        try:
            rel_property = relationship_attr.property
            is_collection = rel_property.uselist
            # Get the target column from the related model
            related_model = rel_property.mapper.class_
            target_column = getattr(related_model, target_field)
        except (AttributeError, NoInspectionAvailable) as e:
            logger.error(f"Error getting relationship property: {e}")
            return None

        if condition.operator in [Operator.exists, Operator.not_exists]:
            # For existence checks, call any()/has() with no arguments
            if is_collection:
                result = relationship_attr.any()
            else:
                result = relationship_attr.has()

            if condition.operator == Operator.not_exists:
                return not_(result)

            return result

        try:
            comparison = self._apply_operator_to_column(
                target_column, condition.operator, condition.value
            )
        except SQLTranslationError:
            comparison = None

        if comparison is None:
            logger.warning(
                f"Unsupported operator {condition.operator} for relationship field {target_field}"
            )
            return None

        # Wrap the comparison in any() or has() based on relationship type
        if is_collection:
            return relationship_attr.any(comparison)

        return relationship_attr.has(comparison)

    def _extract_relationship_target_field(
        self, field_address: FieldAddress, relationship_attr: Any
    ) -> str:
        """Extracts the target field from a relationship field address

        For field_address like 'user.profile.name', extracts 'name' as the target field.
        If no specific field is provided, defaults to the primary key of the related model.

        Args:
            field_address: Parsed field address
            relationship_attr: SQLAlchemy relationship attribute

        Returns:
            Name of the target field to compare against
        """
        # FieldAddress.parse() puts the field name in json_path for 3+ part addresses
        if field_address.json_path and len(field_address.json_path) > 0:
            return field_address.json_path[0]

        # Default to primary key if no specific field provided
        try:
            related_model = relationship_attr.property.mapper.class_
            inspector = inspect(related_model)
            primary_keys = inspector.primary_key
            if primary_keys:
                return primary_keys[0].name
            return self.DEFAULT_PRIMARY_KEY  # Fallback to 'id'
        except NoInspectionAvailable:
            return self.DEFAULT_PRIMARY_KEY  # Safe fallback

    def _handle_property_condition(
        self, model_class: type, field_name: str, prop: Any, condition: ConditionLeaf
    ) -> Optional[Any]:
        """
        Handle conditions on Python properties by finding SQL equivalents

        Args:
            model_class: SQLAlchemy model class
            field_name: Name of the property
            prop: The property object
            condition: The condition being applied

        Returns:
            SQLAlchemy expression or raises an error
        """
        # Since Python properties are computed at runtime, we cannot automatically
        # translate them to SQL without specific knowledge of their implementation.
        # The field name alone doesn't provide enough information to determine
        # the correct SQL translation.

        # If we can't find a SQL equivalent, provide a helpful error with suggestions
        # Get available columns and relationships for better error messages
        try:
            mapper = inspect(model_class)
        except NoInspectionAvailable:
            return None
        available_columns = list(mapper.columns.keys())
        available_relationships = list(mapper.relationships.keys())

        error_msg = (
            f"Property '{field_name}' on {getattr(model_class, '__name__', str(model_class))} cannot be translated to SQL. "
            f"Properties are computed at runtime and don't have direct database equivalents. "
            f"Consider using the underlying database fields instead.\n"
            f"Available columns: {available_columns}\n"
            f"Available relationships: {available_relationships}"
        )

        # Add specific suggestions for common patterns
        if available_relationships:
            error_msg += (
                "\nIf this property is derived from a relationship, "
                "consider using the relationship directly in your condition."
            )

        raise ValueError(error_msg)
