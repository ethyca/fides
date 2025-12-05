from typing import Any, Optional

from pydantic.v1.utils import deep_update

from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.policy import Policy as PolicySchema
from fides.api.task.conditional_dependencies.privacy_request.convenience_fields import (
    get_location_convenience_fields,
    get_policy_convenience_fields,
)
from fides.api.task.conditional_dependencies.privacy_request.schemas import (
    PrivacyRequestLocationConvenienceFields,
)
from fides.api.task.conditional_dependencies.util import (
    extract_nested_field_value,
    set_nested_value,
    transform_value_for_evaluation,
)


class PrivacyRequestDataTransformer:
    """
    Transforms a PrivacyRequest ORM object into a dictionary structure for condition evaluation.

    - This class extracts the fields referenced in conditions and builds a minimal nested structure
    for evaluation. Privacy request fields must be prefixed with the "privacy_request" namespace.
    - This class is used to get the privacy request data for condition evaluation.
        - The task.conditional_dependencies.evaluator expects the data to be in a nested dictionary structure
        and uses the operators defined in the task.conditional_dependencies.operators.py which have defined
        data type compatibility.

    Note: Privacy request relationships are eager loaded in the execute_request_tasks.py file.
    """

    def __init__(self, privacy_request: PrivacyRequest):
        self.privacy_request = privacy_request
        self.policy_data = self._transform_policy_object(privacy_request.policy)
        self.identity_data = self.privacy_request.get_persisted_identity()
        self.custom_privacy_request_fields_data = (
            self.privacy_request.get_persisted_custom_privacy_request_fields()
        )
        self.location_convenience_fields = get_location_convenience_fields(
            privacy_request.location
        )

    def to_evaluation_data(self, field_addresses: set[str]) -> dict[str, Any]:
        """
        Transforms the PrivacyRequest into an evaluation-ready dictionary structure.

        Args:
            field_addresses: Set of field addresses referenced in conditions
        """
        if not field_addresses:
            return {}

        result: dict[str, Any] = {"privacy_request": {}}
        field_paths: set[str] = {addr.replace(":", ".") for addr in field_addresses}

        # Extract each field dynamically based on its path
        for field_path in field_paths:
            value = self._extract_value_by_path(field_path)
            privacy_request_data: Optional[dict[str, Any]] = set_nested_value(
                field_path.split("."), value
            )
            if privacy_request_data:
                result = deep_update(result, privacy_request_data)

        return result

    def _extract_value_by_path(self, field_address: str) -> Any:
        """
        Extracts a value from PrivacyRequest by following the field address path.

        Args:
            field_address: The field address path (e.g., "privacy_request.location", "privacy_request.policy.rules")

        """
        # first part will always be privacy_request
        parts: list[str] = field_address.split(".")[1:]
        current: Any = self.privacy_request
        is_labeled_field = False

        # Handle location convenience fields - these are derived fields, not direct attributes
        # Check if we're accessing a location convenience field before trying to extract from privacy_request

        if len(parts) == 1 and parts[0] in [
            e.value for e in PrivacyRequestLocationConvenienceFields
        ]:
            return self.location_convenience_fields.get(parts[0])

        # Route to the appropriate data source based on the first path component
        if parts[0] == "policy":
            current = self.policy_data
            parts.pop(0)
        elif parts[0] == "identity":
            current = self.identity_data
            # Identity fields may contain LabeledIdentity objects with label/value structure
            is_labeled_field = True
            parts.pop(0)
        elif parts[0] == "custom_privacy_request_fields":
            current = self.custom_privacy_request_fields_data
            # Custom fields are stored as {"label": ..., "value": ...} dicts
            is_labeled_field = True
            parts.pop(0)

        current = extract_nested_field_value(current, parts)

        # If we started with an Identity object and didn't extract any field from it
        # (current is still the identity object), return None
        # Otherwise, transform the value (which could be a BaseModel like LabeledIdentity)
        if current is self.identity_data:
            return None

        # Transform the value first (converts LabeledIdentity to dict, handles other types)
        current = transform_value_for_evaluation(current)

        # For labeled fields (custom privacy request fields and identity fields with labels),
        # extract just the value from the {"label": ..., "value": ...} structure
        if is_labeled_field and isinstance(current, dict) and "value" in current:
            current = current["value"]

        return current

    def _transform_policy_object(self, policy: Policy) -> dict[str, Any]:
        """
        Transforms a Policy ORM object to a dictionary using existing Pydantic schema
        and adds convenience fields.

        Args:
            policy: The Policy ORM object
        """
        if not policy:
            return {}
        extra_fields = get_policy_convenience_fields(policy)

        # Convert Policy ORM object to dictionary using Pydantic schema
        policy_dict = PolicySchema.model_validate(policy).model_dump()
        policy_dict.update(extra_fields)
        return policy_dict
