from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic.v1.utils import deep_update

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import Policy as PolicySchema
from fides.api.task.conditional_dependencies.privacy_request.convenience_fields import (
    get_policy_convenience_fields,
)
from fides.api.task.conditional_dependencies.util import extract_nested_field_value


class PrivacyRequestDataTransformer:
    """
    Transforms a PrivacyRequest ORM object into a dictionary structure for condition evaluation.

    This class extracts the fields referenced in conditions and builds a minimal nested structure
    for evaluation. Privacy request fields must be prefixed with the "privacy_request" namespace.
    """

    def __init__(self, privacy_request: PrivacyRequest):
        self.privacy_request = privacy_request
        self.policy_data = self._transform_policy_object(privacy_request.policy)
        self.identity_data = self.privacy_request.get_persisted_identity()
        self.custom_privacy_request_fields_data = (
            self.privacy_request.get_persisted_custom_privacy_request_fields()
        )

    def to_evaluation_data(self, field_addresses: set[str]) -> dict[str, Any]:
        """
        Transforms the PrivacyRequest into an evaluation-ready dictionary structure.

        Args:
            field_addresses: Set of field addresses referenced in conditions (e.g.,
                {"privacy_request.location", "privacy_request.policy.rules.0.action_type"}).
                Only addresses starting with "privacy_request." or "privacy_request:" are processed.

        Returns:
            A dictionary with the referenced privacy request data under the "privacy_request" key.
        """
        if not field_addresses:
            return {}

        result: dict[str, Any] = {"privacy_request": {}}
        field_paths: set[str] = {addr.replace(":", ".") for addr in field_addresses}

        # Extract each field dynamically based on its path
        for field_path in field_paths:
            value = self._extract_value_by_path(field_path)
            privacy_request_data: Optional[dict[str, Any]] = self._set_nested_value(
                field_path.split("."), value
            )
            if privacy_request_data:
                result = deep_update(result, privacy_request_data)

        return result

    def _extract_value_by_path(self, field_address: str) -> Any:
        """
        Dynamically extract a value from PrivacyRequest by following the field address path.

        This method follows the path through the PrivacyRequest object structure:
        - Direct attributes: "location", "status"
        - Relationship attributes: "policy.key", "policy.name"
        - Method calls: "identity.email", "custom_privacy_request_fields.legal_entity.value"

        Args:
            field_address: The field address path (e.g., "privacy_request.location", "privacy_request.policy.rules")

        """
        # first part will always be privacy_request
        parts: list[str] = field_address.split(".")[1:]
        current: Any = self.privacy_request

        # Track the identity object if we're extracting from identity
        if parts[0] == "policy":
            current = self.policy_data
        elif parts[0] == "identity":
            current = self.identity_data
        elif parts[0] == "custom_privacy_request_fields":
            current = self.custom_privacy_request_fields_data

        if current != self.privacy_request:
            parts.pop(0)

        current = extract_nested_field_value(current, parts)

        # If we started with an Identity object and didn't extract any field from it
        # (current is still the identity object), return None
        # Otherwise, transform the value (which could be a BaseModel like LabeledIdentity)
        if current is not None and current is self.identity_data:
            return None

        return self._transform_value(current)

    def _transform_policy_object(self, policy: Policy) -> dict[str, Any]:
        """
        Transforms a Policy ORM object to a dictionary using existing Pydantic schema
        and adds convenience fields.

        Args:
            policy: The Policy ORM object

        Returns:
            Dictionary representation of the policy with convenience fields added
        """
        if not policy:
            return {}
        extra_fields = get_policy_convenience_fields(policy)

        # Convert Policy ORM object to dictionary using Pydantic schema
        policy_dict = PolicySchema.model_validate(policy).model_dump()
        policy_dict.update(extra_fields)
        return policy_dict

    def _transform_value(self, value: Any) -> Any:
        """
        Transform a value to its evaluation-ready form.

        Args:
            value: The raw value to transform
            field_address: The field address (for context)

        Returns:
            The transformed value
        """
        if value is None:
            return None
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if hasattr(value, "value") and not isinstance(value, BaseModel):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        return value

    def _set_nested_value(
        self, path: list[str], value: Any
    ) -> Optional[dict[str, Any]]:
        """
        Returns a dictionary with a nested value set at the path.

        Args:
            path: List of keys to traverse (e.g., ["policy", "key"])
            value: The value to set at the end of the path
        """
        result: dict[str, Any] = {}
        current = result
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            # Ensure we're still in a dict (no array indexing support)
            if not isinstance(current, dict):
                return None

        # Set the final value
        final_key = path[-1]
        if isinstance(current, dict):
            current[final_key] = value
        return result
