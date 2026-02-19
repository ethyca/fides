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

    def test_tenant_id_with_hyphens(self):
        schema = EntraSchema(
            tenant_id="11111111-2222-3333-4444-555555555555",
            client_id=VALID_CLIENT_ID,
            client_secret=VALID_CLIENT_SECRET,
        )
        assert schema.tenant_id == "11111111-2222-3333-4444-555555555555"

    def test_tenant_id_stripped(self):
        schema = EntraSchema(
            tenant_id=f"  {VALID_TENANT_ID}  ",
            client_id=VALID_CLIENT_ID,
            client_secret=VALID_CLIENT_SECRET,
        )
        assert schema.tenant_id == VALID_TENANT_ID

    def test_tenant_id_invalid_format(self):
        with pytest.raises(ValueError, match="Tenant ID must be a valid Azure AD"):
            EntraSchema(
                tenant_id="not-a-uuid",
                client_id=VALID_CLIENT_ID,
                client_secret=VALID_CLIENT_SECRET,
            )

    def test_tenant_id_empty(self):
        # Base class model_validator (required_components_supplied) runs before field
        # validators and rejects empty required fields with this message.
        with pytest.raises(ValidationError, match="must be supplied all of"):
            EntraSchema(
                tenant_id="",
                client_id=VALID_CLIENT_ID,
                client_secret=VALID_CLIENT_SECRET,
            )

    def test_client_id_invalid_format(self):
        with pytest.raises(ValueError, match="Client ID must be a valid"):
            EntraSchema(
                tenant_id=VALID_TENANT_ID,
                client_id="invalid",
                client_secret=VALID_CLIENT_SECRET,
            )

    def test_client_secret_empty(self):
        with pytest.raises(ValueError, match="Client secret cannot be empty"):
            EntraSchema(
                tenant_id=VALID_TENANT_ID,
                client_id=VALID_CLIENT_ID,
                client_secret="   ",
            )

    def test_missing_required_components(self):
        with pytest.raises(ValueError, match="must be supplied all of"):
            EntraSchema(
                tenant_id=VALID_TENANT_ID,
                client_id=VALID_CLIENT_ID,
                client_secret="",
            )
