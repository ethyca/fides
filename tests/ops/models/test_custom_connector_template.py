from typing import Optional

from sqlalchemy.orm import Session

from fides.api.models.custom_connector_template import CustomConnectorTemplate


class TestCustomConnectorTemplate:
    def test_create_custom_connector_template(
        self,
        db: Session,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ) -> None:
        template = CustomConnectorTemplate(
            key="planet_express",
            name="Planet Express",
            config=planet_express_config,
            dataset=planet_express_dataset,
            icon=planet_express_icon,
            functions=planet_express_functions,
        )
        template.save(db=db)

        # assert we can retrieve a connector template by key and
        # that the values are the same as what we persisted
        custom_connector: Optional[
            CustomConnectorTemplate
        ] = CustomConnectorTemplate.get_by_key_or_id(
            db=db, data={"key": "planet_express"}
        )
        assert custom_connector
        assert custom_connector.name == "Planet Express"
        assert custom_connector.config == planet_express_config
        assert custom_connector.dataset == planet_express_dataset
        assert custom_connector.icon == planet_express_icon
        assert custom_connector.functions == planet_express_functions
