from typing import Any, Dict

from fides.api.schemas.connection_configuration.connection_secrets_sovrn import (
    SOVRN_REQUIRED_IDENTITY,
)
from fides.api.service.connectors.consent_email_connector import (
    GenericConsentEmailConnector,
)


class SovrnConnector(GenericConsentEmailConnector):
    """SovrnConnector - only need to override the details for the test email."""

    @property
    def identities_for_test_email(self) -> Dict[str, Any]:
        return {SOVRN_REQUIRED_IDENTITY: "test_ljt_reader_id"}
