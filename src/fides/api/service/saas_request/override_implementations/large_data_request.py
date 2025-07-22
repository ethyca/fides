from datetime import datetime
from typing import Any, Dict, List

from fides.api.graph.execution import ExecutionNode
from fides.api.models.policy import Policy
from fides.api.models.privacy_request import PrivacyRequest
from fides.api.service.connectors.saas.authenticated_client import AuthenticatedClient
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestType,
    register,
)
from fides.api.util.collection_util import Row


@register("large_data_retrieve", [SaaSRequestType.READ])
def large_data_retrieve(
    client: AuthenticatedClient,
    node: ExecutionNode,
    policy: Policy,
    privacy_request: PrivacyRequest,
    input_data: Dict[str, List[Any]],
    secrets: Dict[str, Any],
) -> List[Row]:
    """
    Generate 1GB of synthetic data to test external storage mechanisms.

    This function creates approximately 1,000,000 records of ~1KB each
    to reach the 1GB threshold and trigger external storage.
    """

    # Each record will be approximately 1KB
    # Target: 1GB = 1,073,741,824 bytes ≈ 1,000,000 records of 1KB each
    num_records = 1_000_000
    base_email = "jane@example.com"

    # Create padding data to reach ~1KB per record
    padding_data = "A" * 800  # 800 characters of padding

    records = []

    for i in range(num_records):
        record = {
            "id": i + 1,
            "email": base_email,
            "name": f"User Name {i + 1:06d}",
            "data": padding_data,
            "created_at": datetime.now().isoformat(),
            "metadata": {
                "field1": f"value_{i + 1}",
                "field2": f"metadata_{i + 1}",
                "large_field": "B" * 100,  # Additional padding
            },
        }
        records.append(record)

        # Log progress every 100,000 records
        if (i + 1) % 100_000 == 0:
            print(f"Generated {i + 1:,} records...")

    print(
        f"Large data test: Generated {len(records):,} records (~{len(records) / 1_000:.1f}MB)"
    )
    return records
