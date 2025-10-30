"""
Service layer for taxonomy management (data_categories, data_uses, data_subjects).
"""

from typing import Any, Dict, List, Literal, Optional, Union, overload

from sqlalchemy import or_
from sqlalchemy.orm import Session

from fides.api.models.event_audit import EventAuditStatus, EventAuditType
from fides.api.models.sql_models import (  # type:ignore[attr-defined]
    DataCategory,
    DataSubject,
    DataUse,
)
from fides.api.models.taxonomy import TaxonomyUsage
from fides.service.event_audit_service import EventAuditService

from .handlers import LegacyTaxonomyHandler, TaxonomyHandler
from .utils import (
    activate_taxonomy_parents,
    check_for_taxonomy_reactivation,
    deactivate_taxonomy_node_and_descendants,
    generate_taxonomy_fides_key,
    handle_taxonomy_reactivation,
    validate_default_taxonomy_restrictions,
    validate_parent_key_exists,
)


class TaxonomyService:
    """
    Taxonomy service for managing Fides taxonomy elements.
    Provides CRUD operations for data_categories, data_uses, and data_subjects.
    """

    # Most of the main methods in this service have a type-specific overload to help with type hints

    def __init__(self, db: Session, event_audit_service: EventAuditService):
        self.db = db
        self.event_audit_service = event_audit_service

    @overload
    def get_elements(
        self,
        taxonomy_type: Literal["data_category"],
        active_only: bool = True,
        parent_key: Optional[str] = None,
    ) -> List[DataCategory]: ...

    @overload
    def get_elements(
        self,
        taxonomy_type: Literal["data_use"],
        active_only: bool = True,
        parent_key: Optional[str] = None,
    ) -> List[DataUse]: ...

    @overload
    def get_elements(
        self,
        taxonomy_type: Literal["data_subject"],
        active_only: bool = True,
        parent_key: Optional[str] = None,
    ) -> List[DataSubject]: ...

    def get_elements(
        self,
        taxonomy_type: str,
        active_only: bool = True,
        parent_key: Optional[str] = None,
    ) -> List[Union[DataCategory, DataUse, DataSubject]]:
        """Get elements for a taxonomy type."""
        return self._get_handler(taxonomy_type).get_elements(active_only, parent_key)

    @overload
    def get_element(
        self, taxonomy_type: Literal["data_category"], fides_key: str
    ) -> Optional[DataCategory]: ...

    @overload
    def get_element(
        self, taxonomy_type: Literal["data_use"], fides_key: str
    ) -> Optional[DataUse]: ...

    @overload
    def get_element(
        self, taxonomy_type: Literal["data_subject"], fides_key: str
    ) -> Optional[DataSubject]: ...

    def get_element(self, taxonomy_type: str, fides_key: str) -> Optional[Any]:
        """Get a single element by fides_key."""
        return self._get_handler(taxonomy_type).get_element(fides_key)

    @overload
    def create_element(
        self, taxonomy_type: Literal["data_category"], element_data: Dict
    ) -> DataCategory: ...

    @overload
    def create_element(
        self, taxonomy_type: Literal["data_use"], element_data: Dict
    ) -> DataUse: ...

    @overload
    def create_element(
        self, taxonomy_type: Literal["data_subject"], element_data: Dict
    ) -> DataSubject: ...

    def create_element(
        self, taxonomy_type: str, element_data: Dict
    ) -> Union[DataCategory, DataUse, DataSubject]:
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

        element = self._get_handler(taxonomy_type).create_element(processed_data)

        self.event_audit_service.create_event_audit(
            EventAuditType.taxonomy_element_created,
            EventAuditStatus.succeeded,
            resource_type="taxonomy_element",
            resource_identifier=processed_data.get("fides_key"),
            description=f"Created {taxonomy_type} element: {processed_data.get('fides_key')} ({processed_data.get('name')})",
            event_details={
                "taxonomy_type": taxonomy_type,
                **processed_data,
            },
        )

        return element

    @overload
    def update_element(
        self,
        taxonomy_type: Literal["data_category"],
        fides_key: str,
        element_data: Dict,
    ) -> Optional[DataCategory]: ...

    @overload
    def update_element(
        self, taxonomy_type: Literal["data_use"], fides_key: str, element_data: Dict
    ) -> Optional[DataUse]: ...

    @overload
    def update_element(
        self,
        taxonomy_type: Literal["data_subject"],
        fides_key: str,
        element_data: Dict,
    ) -> Optional[DataSubject]: ...

    def update_element(
        self, taxonomy_type: str, fides_key: str, element_data: Dict
    ) -> Optional[Any]:
        """Update an existing taxonomy element."""
        # Get the existing element for validation
        handler = self._get_handler(taxonomy_type)
        existing_element = handler.get_element(fides_key)

        self._validate_element_data(
            element_data,
            taxonomy_type,
            existing_element=existing_element,
            action="update",
        )

        # Update the element via handler
        updated_element = handler.update_element(fides_key, element_data)

        # Return early if element was not found
        if updated_element is None:
            return None

        # Handle hierarchical activation/deactivation logic at service level
        if "active" in element_data:
            if element_data["active"]:
                activate_taxonomy_parents(updated_element, self.db)
            else:
                # Cascade down - deactivate current node and children
                deactivate_taxonomy_node_and_descendants(updated_element, self.db)

            # Ensure hierarchical updates are visible across sessions
            # The model's own update() commits, but parent/child mutations above
            # only flush by design. Commit here so other sessions (e.g., API tests)
            # can observe the propagated changes immediately.
            self.db.commit()
            # Refresh the updated element to return the latest state
            self.db.refresh(updated_element)

        self.event_audit_service.create_event_audit(
            EventAuditType.taxonomy_element_updated,
            EventAuditStatus.succeeded,
            resource_type="taxonomy_element",
            resource_identifier=fides_key,
            description=f"Updated {taxonomy_type} element: {fides_key} ({updated_element.name})",  # type: ignore
            event_details={
                "taxonomy_type": taxonomy_type,
                **element_data,
            },
        )

        return updated_element

    def delete_element(self, taxonomy_type: str, fides_key: str) -> None:
        """Delete a taxonomy element."""
        # First, remove any TaxonomyUsage rows that reference this element
        # as either the source or the target element. There is no DB cascade
        # for these relationships by design, so this cleanup is handled here.
        self.db.query(TaxonomyUsage).filter(
            or_(
                TaxonomyUsage.source_element_key == fides_key,
                TaxonomyUsage.target_element_key == fides_key,
            )
        ).delete(synchronize_session=False)

        # Then delete the element itself via the appropriate handler
        self._get_handler(taxonomy_type).delete_element(fides_key)
        self.db.commit()

        self.event_audit_service.create_event_audit(
            EventAuditType.taxonomy_element_deleted,
            EventAuditStatus.succeeded,
            resource_type="taxonomy_element",
            resource_identifier=fides_key,
            description=f"Deleted {taxonomy_type} element: {fides_key}",
            event_details={
                "taxonomy_type": taxonomy_type,
                "fides_key": fides_key,
            },
        )

    @overload
    def create_or_update_element(
        self, taxonomy_type: Literal["data_category"], element_data: Dict
    ) -> DataCategory: ...

    @overload
    def create_or_update_element(
        self, taxonomy_type: Literal["data_use"], element_data: Dict
    ) -> DataUse: ...

    @overload
    def create_or_update_element(
        self, taxonomy_type: Literal["data_subject"], element_data: Dict
    ) -> DataSubject: ...

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

        return self.create_element(taxonomy_type, element_data)  # type: ignore[call-overload]

    def _get_handler(self, taxonomy_type: str) -> TaxonomyHandler:
        """Get the handler for taxonomy operations."""
        return LegacyTaxonomyHandler(self.db, taxonomy_type)

    def _validate_element_data(
        self,
        element_data: Dict,
        taxonomy_type: str,
        existing_element: Optional[Union[DataCategory, DataUse, DataSubject]] = None,
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
                taxonomy_type, element_data["parent_key"], handler
            )
