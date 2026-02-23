from datetime import datetime, timezone

import factory

from fides.api.models.privacy_request import PrivacyRequest
from fides.api.schemas.privacy_request import PrivacyRequestStatus
from tests.factories.base import BaseFactory


class PrivacyRequestFactory(BaseFactory):
    class Meta:
        model = PrivacyRequest

    external_id = factory.LazyFunction(
        lambda: f"ext-{factory.Faker('uuid4').generate()}"
    )
    status = PrivacyRequestStatus.in_processing
    requested_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    policy_id = factory.LazyAttribute(lambda o: o.policy.id if o.policy else None)

    class Params:
        policy = None
