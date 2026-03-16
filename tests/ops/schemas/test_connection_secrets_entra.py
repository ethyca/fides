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

    def test_whitespace_only_tenant_id_fails(self):
        with pytest.raises(ValidationError, match="Tenant ID cannot be empty"):
            EntraSchema(
                tenant_id="   ",
                client_id=VALID_CLIENT_ID,
                client_secret=VALID_CLIENT_SECRET,
            )

    def test_whitespace_only_client_id_fails(self):
        with pytest.raises(ValidationError, match="Client ID cannot be empty"):
            EntraSchema(
                tenant_id=VALID_TENANT_ID,
                client_id="   ",
                client_secret=VALID_CLIENT_SECRET,
            )

    def test_whitespace_only_client_secret_fails(self):
        with pytest.raises(ValidationError, match="Client secret cannot be empty"):
            EntraSchema(
                tenant_id=VALID_TENANT_ID,
                client_id=VALID_CLIENT_ID,
                client_secret="   ",
            )

    def test_invalid_uuid_tenant_id_fails(self):
        with pytest.raises(ValidationError, match="Invalid tenant ID"):
            EntraSchema(
                tenant_id="not-a-uuid",
                client_id=VALID_CLIENT_ID,
                client_secret=VALID_CLIENT_SECRET,
            )

    def test_invalid_uuid_client_id_fails(self):
        with pytest.raises(ValidationError, match="Invalid client ID"):
            EntraSchema(
                tenant_id=VALID_TENANT_ID,
                client_id="not-a-uuid",
                client_secret=VALID_CLIENT_SECRET,
            )

    def test_client_secret_uuid_rejected(self):
        """Pasting the secret ID (a UUID) instead of the secret value is rejected."""
        with pytest.raises(ValidationError, match="Client secret appears to be a UUID"):
            EntraSchema(
                tenant_id=VALID_TENANT_ID,
                client_id=VALID_CLIENT_ID,
                client_secret="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            )

    def test_whitespace_stripped_from_all_fields(self):
        schema = EntraSchema(
            tenant_id=f"  {VALID_TENANT_ID}  ",
            client_id=f"\t{VALID_CLIENT_ID}\t",
            client_secret=f"  {VALID_CLIENT_SECRET}  ",
        )
        assert schema.tenant_id == VALID_TENANT_ID
        assert schema.client_id == VALID_CLIENT_ID
        assert schema.client_secret == VALID_CLIENT_SECRET
