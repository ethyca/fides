"""Tests for Microsoft Entra ID connection secrets schema."""

import pytest
from pydantic import ValidationError

from fides.api.schemas.connection_configuration import EntraSchema

VALID_TENANT_ID = "11111111-2222-3333-4444-555555555555"
VALID_CLIENT_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
VALID_CLIENT_SECRET = "my-secret-value"


class TestEntraSchema:
    """Validation tests for EntraSchema."""

    def test_valid_secrets(self):
        schema = EntraSchema(
            tenant_id=VALID_TENANT_ID,
            client_id=VALID_CLIENT_ID,
            client_secret=VALID_CLIENT_SECRET,
        )
        assert schema.tenant_id == VALID_TENANT_ID
        assert schema.client_id == VALID_CLIENT_ID
        assert schema.client_secret == VALID_CLIENT_SECRET

    def test_missing_required_components(self):
        with pytest.raises(ValidationError, match="must be supplied all of"):
            EntraSchema(
                tenant_id=VALID_TENANT_ID,
                client_id=VALID_CLIENT_ID,
                client_secret="",
            )

    def test_all_fields_empty(self):
        with pytest.raises(ValidationError, match="must be supplied all of"):
            EntraSchema(
                tenant_id="",
                client_id="",
                client_secret="",
            )
