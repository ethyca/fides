import factory

from fides.api.models.fides_user import FidesUser
from tests.factories.base import BaseFactory


class FidesUserFactory(BaseFactory):
    class Meta:
        model = FidesUser

    username = factory.Sequence(lambda n: f"test_user_{n}")
    email_address = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
