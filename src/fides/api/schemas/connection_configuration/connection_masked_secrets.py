from __future__ import annotations

from typing import Any, Dict, cast

from pydantic import root_validator, BaseModel

# from fides.api.schemas.connection_configuration.connection_secrets import ConnectionConfigSecretsSchema
from fides.api.util.connection_type import get_connection_type_secret_schema



class ConnectionConfigMaskedSecrets(BaseModel):
    """Schema that masks sensitive values in the response."""


