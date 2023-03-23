from typing import Optional

import pytest
from sqlalchemy.orm import Session

from fides.api.ops.models.custom_connector_template import CustomConnectorTemplate
from fides.api.ops.util.saas_util import (
    encode_file_contents,
    load_as_string,
    load_yaml_as_string,
)


class TestCustomConnectorTemplate:
    def test_create_custom_connector_template(
        self, db: Session, custom_config, custom_dataset, custom_icon, custom_functions
    ) -> None:
        template = CustomConnectorTemplate(
            key="custom",
            name="Custom",
            config=custom_config,
            dataset=custom_dataset,
            icon=custom_icon,
            functions=custom_functions,
        )
        template.save(db=db)

        # assert we can retrieve a connector template by key and
        # that the values are the same as what we persisted
        custom_connector: Optional[
            CustomConnectorTemplate
        ] = CustomConnectorTemplate.get_by_key_or_id(db=db, data={"key": "custom"})
        assert custom_connector
        assert custom_connector.name == "Custom"
        assert custom_connector.config == custom_config
        assert custom_connector.dataset == custom_dataset
        assert custom_connector.icon == custom_icon
        assert custom_connector.functions == custom_functions
