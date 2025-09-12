from typing import Optional

from collections import deque
from loguru import logger
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

    def analyze_tables_in_condition(
        self, condition: Condition
    ) -> dict[str, list[FieldAddress]]:
        """
        Analyze which tables are referenced in a condition and group field addresses by table

        Args:
            condition: The condition to analyze

        Returns:
            Dictionary mapping table names to lists of field addresses for that table
            (preserves order of first appearance)
        """
        field_addresses = self.extract_field_addresses(condition)

        # Group field addresses by table, preserving order of first appearance
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

        Uses SQLAlchemy's registry and metadata for efficient lookups.

        Args:
            table_name: Database table name

        Returns:
            SQLAlchemy model class or None if not found
        """
        # Check cache first
        if table_name in self._model_cache:
            return self._model_cache[table_name]

        # This approach works for SQLAlchemy 1.4+ using the registry.
        if hasattr(self.orm_registry, 'registry') and hasattr(self.orm_registry.registry, '_class_registry'):
            try:
                # SQLAlchemy 1.4+ uses registry.mappers or registry._class_registry
                if hasattr(self.orm_registry.registry, 'mappers'):
                    for mapper in self.orm_registry.registry.mappers:
                        if mapper.class_.__tablename__ == table_name:
                            self._model_cache[table_name] = mapper.class_
                            return mapper.class_
                # else:
                #     # Try the _class_registry approach
                #     for model_class in self.orm_registry.registry._class_registry.data.values():
                #         if (hasattr(model_class, '__tablename__')
                #             and getattr(model_class, '__tablename__', None) == table_name):
                #             self._model_cache[table_name] = model_class
                #             return model_class
            except (AttributeError, TypeError) as e:
                logger.debug(f"Registry approach failed: {e}")

        # If not found, cache None and return
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

        # For join/reference tables, try to find their related main tables
        model_classes = self._expand_with_related_main_tables(
            model_classes, tables_to_fields
        )

        if not model_classes:
            raise SQLTranslationError(
                "No valid SQLAlchemy models found for the specified tables"
            )

        # Determine primary model (most connected or first alphabetically)
        primary_table = self._determine_primary_table(model_classes, tables_to_fields)
        primary_model = model_classes[primary_table]

        # Build base query - select from primary model (equivalent to SELECT *)
        query = self.db.query(primary_model)

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
        """
        Determine which model should be the primary query target

        Strategy:
        1. Use the table from the first condition (most intuitive for users)
        2. Prefer "main" entities over join/reference tables
        3. Use the table with the most fields in conditions
        4. Fall back to first alphabetically
        """
        # Strategy 1: Use the table from the first condition
        # This makes the query intent clear and predictable for users
        if tables_to_fields:
            first_table_name = next(iter(tables_to_fields.keys()))
            if first_table_name in model_classes:
                logger.debug(f"Using first condition table '{first_table_name}' as primary table")
                return first_table_name

        # Common patterns for join/reference table names
        join_table_patterns = ["_reference", "_join", "_link", "_assoc", "_association"]

        # Separate main tables from potential join tables
        main_tables = []
        join_tables = []

        for table_name in tables_to_fields.keys():
            if table_name in model_classes:
                is_join_table = any(
                    pattern in table_name.lower() for pattern in join_table_patterns
                )
                if is_join_table:
                    join_tables.append(table_name)
                else:
                    main_tables.append(table_name)

        # Prefer main tables over join tables
        candidate_tables = main_tables if main_tables else join_tables

        # Among candidates, use the table with the most fields in conditions
        max_fields = 0
        primary_table = None

        for table_name in candidate_tables:
            fields = tables_to_fields.get(table_name, [])
            if len(fields) > max_fields:
                max_fields = len(fields)
                primary_table = table_name

        # Fall back to first alphabetically from all available tables
        return primary_table or sorted(model_classes.keys())[0]

    def _expand_with_related_main_tables(
        self, model_classes: dict[str, type], tables_to_fields: dict[str, list]
    ) -> dict[str, type]:
        """
        For join/reference tables, find and include their related main tables

        This helps with relationship queries where conditions are on join tables
        but we want to return records from the main entities.
        """
        join_table_patterns = ["_reference", "_join", "_link", "_assoc", "_association"]
        expanded_model_classes = model_classes.copy()

        for table_name, model_class in model_classes.items():
            # Check if this looks like a join table
            is_join_table = any(
                pattern in table_name.lower() for pattern in join_table_patterns
            )

            if is_join_table:
                # Try to find related main tables through relationships
                main_tables = self._find_related_main_tables(model_class, table_name)
                for main_table_name, main_model_class in main_tables.items():
                    if main_table_name not in expanded_model_classes:
                        expanded_model_classes[main_table_name] = main_model_class
                        # Add empty field list for the main table since it wasn't in conditions
                        tables_to_fields[main_table_name] = []

        return expanded_model_classes

    def _find_related_main_tables(
        self, join_model_class: type, join_table_name: str
    ) -> dict[str, type]:
        """
        Find main tables that have relationships to this join table

        For example, if we have ManualTaskReference, find ManualTask
        """
        related_tables = {}

        try:
            mapper = inspect(join_model_class)

            # Look at relationships from the join table to find main tables
            for relationship_name, relationship_prop in mapper.relationships.items():
                if hasattr(relationship_prop, "mapper"):
                    target_model = relationship_prop.mapper.class_
                    target_table_name = getattr(target_model, "__tablename__", None)

                    if target_table_name and target_table_name != join_table_name:
                        # Check if this looks like a main table (not another join table)
                        join_patterns = [
                            "_reference",
                            "_join",
                            "_link",
                            "_assoc",
                            "_association",
                        ]
                        is_main_table = not any(
                            pattern in target_table_name.lower()
                            for pattern in join_patterns
                        )

                        if is_main_table:
                            related_tables[target_table_name] = target_model

        except Exception:
            # If inspection fails, continue without adding related tables
            pass

        return related_tables

    def _find_relationship_path_through_intermediates(
        self, from_model: type, to_model: type, max_depth: int = 3
    ) -> Optional[list]:
        """
        Find relationship path between models, including through intermediate tables

        Uses breadth-first search to find the shortest path through relationships.
        This can discover paths like: ManualTask -> ManualTaskReference -> FidesUser

        Args:
            from_model: Source model class
            to_model: Target model class
            max_depth: Maximum relationship hops to explore

        Returns:
            List of relationship attributes to traverse, or None if no path found
        """
        if from_model == to_model:
            return []

        # Use BFS to find shortest relationship path
        # Queue items: (current_model, path_so_far)
        queue = deque([(from_model, [])])
        visited = {from_model}

        for _ in range(max_depth):
            if not queue:
                break

            for _ in range(len(queue)):
                current_model, current_path = queue.popleft()

                try:

                    mapper = inspect(current_model)

                    # Explore all relationships from current model
                    for (
                        relationship_name,
                        relationship_prop,
                    ) in mapper.relationships.items():
                        if hasattr(relationship_prop, "mapper"):
                            next_model = relationship_prop.mapper.class_

                            # Found target model!
                            if next_model == to_model:
                                return current_path + [
                                    getattr(current_model, relationship_name)
                                ]

                            # Add to queue for further exploration if not visited
                            if next_model not in visited:
                                visited.add(next_model)
                                queue.append(
                                    (
                                        next_model,
                                        current_path
                                        + [getattr(current_model, relationship_name)],
                                    )
                                )

                except Exception:
                    # Skip if inspection fails
                    continue

        return None

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

            # Try to find direct relationship path first
            join_path = self._find_relationship_path(primary_model, model_class)

            if join_path:
                # Apply JOINs using the direct relationship path
                for relationship_attr in join_path:
                    query = query.join(relationship_attr)
            else:
                # Try to find path through intermediate tables
                join_path = self._find_relationship_path_through_intermediates(
                    primary_model, model_class, max_depth=3
                )

                if join_path:
                    # Apply JOINs using the intermediate relationship path
                    for relationship_attr in join_path:
                        query = query.join(relationship_attr)
                else:
                    # Try to find any model that can reach this one (fallback)
                    joined = False
                    for joined_table, joined_model in model_classes.items():
                        if joined_table == table_name or joined_table == primary_table:
                            continue

                        path = self._find_relationship_path_through_intermediates(
                            joined_model, model_class, max_depth=2
                        )
                        if path:
                            for relationship_attr in path:
                                query = query.join(relationship_attr)
                            joined = True
                            break

                    if not joined:
                        # Log warning but don't fail - the query might still work
                        # This is where the cartesian product warning comes from
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
            # Regular column or relationship
            if hasattr(model_class, field_addr.base_field_name):
                attr = getattr(model_class, field_addr.base_field_name)

                # Check what type of attribute this is and handle accordingly
                return self._handle_model_attribute(
                    model_class, field_addr.base_field_name, attr, condition
                )

        return None

    def _handle_model_attribute(self, model_class: type, field_name: str, attr, condition):
        """
        Handle different types of model attributes (columns, relationships, properties)

        Args:
            model_class: SQLAlchemy model class
            field_name: Name of the field
            attr: The attribute from getattr(model_class, field_name)
            condition: The condition being applied

        Returns:
            SQLAlchemy expression or None
        """
        from sqlalchemy.ext.hybrid import hybrid_property
        from sqlalchemy.orm import RelationshipProperty
        from sqlalchemy import inspect

        # Check if it's a SQLAlchemy column
        if hasattr(attr, 'property') and hasattr(attr.property, 'columns'):
            logger.debug(f"Found column {field_name} on {model_class.__name__}")
            return self._apply_operator_to_column(attr, condition.operator, condition.value)

        # Check if it's a relationship
        elif hasattr(attr, 'property') and isinstance(attr.property, RelationshipProperty):
            logger.debug(f"Found relationship {field_name} on {model_class.__name__}")
            return self._handle_relationship_condition(attr, condition)

        # Check if it's a hybrid property (can be translated to SQL)
        elif isinstance(attr, hybrid_property):
            logger.debug(f"Found hybrid property {field_name} on {model_class.__name__}")
            return self._apply_operator_to_column(attr, condition.operator, condition.value)

        # Check if it's a regular property
        elif isinstance(attr, property):
            logger.debug(f"Found property {field_name} on {model_class.__name__}")
            # Try to find a SQL equivalent for the property
            return self._handle_property_condition(model_class, field_name, attr, condition)

        # Default: treat as a column
        else:
            logger.debug(f"Treating {field_name} as column on {model_class.__name__}")
            return self._apply_operator_to_column(attr, condition.operator, condition.value)

    def _handle_relationship_condition(self, relationship_attr, condition):
        """
        Handle conditions on relationships using SQLAlchemy's any() method

        Args:
            relationship_attr: SQLAlchemy relationship attribute
            condition: The condition being applied

        Returns:
            SQLAlchemy expression using any() or has()
        """
        from sqlalchemy.orm import RelationshipProperty

        # For list_contains on relationships, we want to check if any related object matches
        if condition.operator == Operator.list_contains:
            # Use any() to check if any related object has the specified value
            # This assumes the relationship points to objects with an 'id' field
            return relationship_attr.any(id=condition.value)
        elif condition.operator == Operator.eq:
            # For equality, check if the relationship has an object with this value
            return relationship_attr.any(id=condition.value)
        else:
            logger.warning(f"Unsupported operator {condition.operator} for relationship")
            return None

    def _handle_property_condition(self, model_class: type, field_name: str, prop, condition):
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
        # Special handling for known property patterns
        if field_name == 'assigned_users':
            # For assigned_users property, translate to a query on the references relationship
            if hasattr(model_class, 'references'):
                references_attr = getattr(model_class, 'references')

                if condition.operator == Operator.list_contains:
                    # Check if any reference has this user ID and is an assigned_user type
                    return references_attr.any(
                        (references_attr.property.mapper.class_.reference_id == condition.value) &
                        (references_attr.property.mapper.class_.reference_type == 'assigned_user')
                    )

        # If we can't find a SQL equivalent, provide a helpful error
        raise ValueError(
            f"Property '{field_name}' on {model_class.__name__} cannot be translated to SQL. "
            f"Consider using the underlying database fields instead. "
            f"For assigned_users, use manual_task_reference.reference_id and manual_task_reference.reference_type."
        )

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
