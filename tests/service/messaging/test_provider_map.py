"""_PROVIDER_MAP completeness invariant test.

Ensures every MessagingServiceType value has a corresponding provider class
in the dispatch provider map. If a new service type is added without a
provider, this test catches it.
"""

from fides.api.schemas.messaging.messaging import MessagingServiceType
from fides.api.service.messaging.message_dispatch_service import _PROVIDER_MAP


class TestProviderMapCompleteness:
    def test_all_service_types_have_providers(self):
        assert set(_PROVIDER_MAP.keys()) == set(MessagingServiceType)
