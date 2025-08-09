"""
Service layer for taxonomy management (data_categories, data_uses, data_subjects).
"""

from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session

from .handlers import LegacyTaxonomyHandler
from .utils import (
    activate_taxonomy_parents,
    check_for_taxonomy_reactivation,
    deactivate_taxonomy_node_and_descendants,
    generate_taxonomy_fides_key,
    handle_taxonomy_reactivation,
    validate_default_taxonomy_restrictions,
    validate_parent_key_exists,
)

from fides.api.models.taxonomy import LEGACY_TAXONOMIES


class TaxonomyService:
    """
    Taxonomy service for managing Fides taxonomy elements.
    Provides CRUD operations for data_categories, data_uses, and data_subjects.
    """

    def __init__(self, db: Session):
        self.db = db
        self._legacy_handler = LegacyTaxonomyHandler(db)

    def get_elements(
        self,
        taxonomy_type: str,
        active_only: bool = True,
        parent_key: Optional[str] = None,
    ) -> List[Any]:
        """Get elements for a taxonomy type."""
        return self._get_handler(taxonomy_type).get_elements(
            taxonomy_type, active_only, parent_key
        )

    def get_element(self, taxonomy_type: str, fides_key: str) -> Optional[Any]:
        """Get a single element by fides_key."""
        return self._get_handler(taxonomy_type).get_element(taxonomy_type, fides_key)

    def create_element(self, taxonomy_type: str, element_data: Dict) -> Any:
        """Create a new taxonomy element."""
        # Generate fides_key if not provided
        processed_data = element_data.copy()
        if not processed_data.get("fides_key") and processed_data.get("name"):
            handler = self._get_handler(taxonomy_type)
            processed_data["fides_key"] = generate_taxonomy_fides_key(
                taxonomy_type,
                processed_data["name"],
                processed_data.get("parent_key"),
                handler,
            )

        # Centralized validation before delegation
        self._validate_element_data(processed_data, taxonomy_type, action="create")
        return self._get_handler(taxonomy_type).create_element(
            taxonomy_type, processed_data
        )

    def update_element(
        self, taxonomy_type: str, fides_key: str, element_data: Dict
    ) -> Optional[Any]:
        """Update an existing taxonomy element."""
        # Get the existing element for validation
        handler = self._get_handler(taxonomy_type)
        model_class = handler.get_model(taxonomy_type)
        existing_element = (
            self.db.query(model_class)
            .filter(model_class.fides_key == fides_key)
            .first()
        )
        if existing_element:
            # Centralized validation before delegation
            self._validate_element_data(
                element_data,
                taxonomy_type,
                existing_element=existing_element,
                action="update",
            )

        # Update the element via handler
        updated_element = self._get_handler(taxonomy_type).update_element(
            taxonomy_type, fides_key, element_data
        )

        # Handle hierarchical activation/deactivation logic at service level
        if updated_element and "active" in element_data:
            if element_data["active"]:
                activate_taxonomy_parents(updated_element, self.db)
            else:
                # Cascade down - deactivate current node and children
                deactivate_taxonomy_node_and_descendants(updated_element, self.db)

        return updated_element

    def delete_element(self, taxonomy_type: str, fides_key: str) -> bool:
        """Delete a taxonomy element."""
        return self._get_handler(taxonomy_type).delete_element(taxonomy_type, fides_key)

    def create_or_update_element(self, taxonomy_type: str, element_data: Dict) -> Any:
        """
        Create or update a taxonomy element.
        If the element is deactivated, it will be updated and re-activated, along with its parents.
        This method provides compatibility with the existing generic_overrides endpoint pattern.
        """
        # Check for reactivation case centrally
        handler = self._get_handler(taxonomy_type)
        reactivation_element = check_for_taxonomy_reactivation(
            self.db, taxonomy_type, element_data, handler
        )

        if reactivation_element:
            return handle_taxonomy_reactivation(
                self.db, taxonomy_type, reactivation_element, element_data, handler
            )

        return self.create_element(taxonomy_type, element_data)

    def _get_handler(self, taxonomy_type: str) -> LegacyTaxonomyHandler:
        """Get the handler for taxonomy operations."""
        # Only legacy taxonomies are supported
        if taxonomy_type not in LEGACY_TAXONOMIES:
            raise ValueError(
                f"Taxonomy type '{taxonomy_type}' not supported. "
                f"Supported taxonomy types: {list(LEGACY_TAXONOMIES)}"
            )
        return self._legacy_handler

    def _validate_element_data(
        self,
        element_data: Dict,
        taxonomy_type: str,
        existing_element: Optional[Union[Dict, Any]] = None,
        action: str = "create",
    ) -> None:
        """
        Centralized validation for taxonomy elements.
        This runs before delegation to ensure consistent validation across all handlers.
        """
        # Validate default taxonomy restrictions for taxonomy elements
        if action == "create":
            validate_default_taxonomy_restrictions(element_data, action="create")
        elif action == "update" and existing_element:
            validate_default_taxonomy_restrictions(
                element_data, resource=existing_element, action="update"
            )

        # Validate parent_key exists if provided
        if "parent_key" in element_data and element_data["parent_key"]:
            handler = self._get_handler(taxonomy_type)
            validate_parent_key_exists(
                self.db, taxonomy_type, element_data["parent_key"], handler
            )
