import factory

from fides.api.models.datasetconfig import DatasetConfig
from tests.factories.base import BaseFactory


class DatasetConfigFactory(BaseFactory):
    class Meta:
        model = DatasetConfig

    fides_key = factory.Sequence(lambda n: f"test_dataset_{n}")
    connection_config_id = factory.LazyAttribute(
        lambda o: o.connection_config.id if o.connection_config else None
    )
    ctl_dataset_id = factory.LazyAttribute(
        lambda o: o.ctl_dataset.id if o.ctl_dataset else None
    )

    class Params:
        connection_config = None
        ctl_dataset = None
