import factory

from fides.api.models.sql_models import System
from tests.factories.base import BaseFactory


class SystemFactory(BaseFactory):
    class Meta:
        model = System

    fides_key = factory.Sequence(lambda n: f"test_system_{n}")
    system_type = "Service"
    name = factory.Sequence(lambda n: f"Test System {n}")
    organization_fides_key = "default_organization"
