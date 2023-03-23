import os

import pytest

from fides.api.ops.common_exceptions import NoSuchSaaSRequestOverrideException
from fides.api.ops.models.custom_connector_template import CustomConnectorTemplate
from fides.api.ops.schemas.saas.connector_template import ConnectorTemplate
from fides.api.ops.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.ops.service.connectors.saas.connector_registry_service import (
    CustomConnectorTemplateLoader,
    FileConnectorTemplateLoader,
    register_custom_functions,
)
from fides.api.ops.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
)
from fides.api.ops.util.saas_util import encode_file_contents, load_yaml_as_string
from fides.core.config import CONFIG


class TestFileConnectorTemplateLoader:
    def test_file_connector_template_loader(self):
        loader = FileConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()

        assert connector_templates

        mailchimp_connector = connector_templates.get("mailchimp")
        assert mailchimp_connector

        assert mailchimp_connector.config == load_yaml_as_string(
            "data/saas/config/mailchimp_config.yml"
        )
        assert mailchimp_connector.dataset == load_yaml_as_string(
            "data/saas/dataset/mailchimp_dataset.yml"
        )
        assert mailchimp_connector.icon == encode_file_contents(
            "data/saas/icon/mailchimp.svg"
        )
        assert mailchimp_connector.human_readable == "Mailchimp"

    def test_file_connector_template_loader_connector_not_found(self):
        loader = FileConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()

        assert connector_templates.get("not_found") is None


class TestCustomConnectorTemplateLoader:
    def test_file_connector_template_loader_no_templates(self):
        loader = CustomConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()
        assert connector_templates == {}

    def test_file_connector_template_loader_invalid_template(
        self, db, custom_dataset, custom_icon, custom_functions
    ):
        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="custom",
            name="Custom",
            config="custom_config",
            dataset=custom_dataset,
            icon=custom_icon,
            functions=custom_functions,
        )
        custom_template.save(db=db)

        # verify the custom functions aren't loaded if the template is invalid
        loader = CustomConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()
        assert connector_templates == {}

        with pytest.raises(NoSuchSaaSRequestOverrideException):
            SaaSRequestOverrideFactory.get_override(
                "custom_user_access", SaaSRequestType.READ
            )

        # assert the strategy was not registered
        authentication_strategies = AuthenticationStrategy.get_strategies()
        assert "custom" not in [strategy.name for strategy in authentication_strategies]

    def test_file_connector_template_loader_invalid_functions(
        self, db, custom_config, custom_dataset, custom_icon
    ):
        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="custom",
            name="Custom",
            config=custom_config,
            dataset=custom_dataset,
            icon=custom_icon,
            functions="custom_functions",
        )
        custom_template.save(db=db)

        # verify nothing is loaded if the custom functions fail to load
        loader = CustomConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()
        assert connector_templates == {}

    def test_file_connector_template_loader_custom_connector_functions_disabled(
        self, db, custom_config, custom_dataset, custom_icon, custom_functions
    ):
        CONFIG.security.allow_custom_connector_functions = False

        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="custom",
            name="Custom",
            config=custom_config,
            dataset=custom_dataset,
            icon=custom_icon,
            functions=custom_functions,
        )
        custom_template.save(db=db)

        # load custom connector templates from the database
        loader = CustomConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()
        assert connector_templates == {}

        with pytest.raises(NoSuchSaaSRequestOverrideException):
            SaaSRequestOverrideFactory.get_override(
                "custom_user_access", SaaSRequestType.READ
            )

        # assert the strategy was not registered
        authentication_strategies = AuthenticationStrategy.get_strategies()
        assert "custom" not in [strategy.name for strategy in authentication_strategies]

        CONFIG.security.allow_custom_connector_functions = True

    def test_file_connector_template_loader_custom_connector_functions_disabled_no_custom_functions(
        self, db, custom_config, custom_dataset, custom_icon
    ):
        """
        A connector template with no custom functions should still be loaded
        even if allow_custom_connector_functions is set to false
        """

        CONFIG.security.allow_custom_connector_functions = False

        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="custom",
            name="Custom",
            config=custom_config,
            dataset=custom_dataset,
            icon=custom_icon,
            functions=None,
        )
        custom_template.save(db=db)

        # load custom connector templates from the database
        loader = CustomConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()
        assert connector_templates == {
            "custom": ConnectorTemplate(
                config=custom_config,
                dataset=custom_dataset,
                icon=custom_icon,
                human_readable="Custom",
            )
        }

        CONFIG.security.allow_custom_connector_functions = True

    def test_file_connector_template_loader(
        self, db, custom_config, custom_dataset, custom_icon, custom_functions
    ):
        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="custom",
            name="Custom",
            config=custom_config,
            dataset=custom_dataset,
            icon=custom_icon,
            functions=custom_functions,
        )
        custom_template.save(db=db)

        # load custom connector templates from the database
        loader = CustomConnectorTemplateLoader()
        connector_templates = loader.get_connector_templates()

        # verify that the template in the registry is the same as the one in the database
        assert connector_templates == {
            "custom": ConnectorTemplate(
                config=custom_config,
                dataset=custom_dataset,
                icon=custom_icon,
                human_readable="Custom",
            )
        }

        # assert the request override was registered
        SaaSRequestOverrideFactory.get_override(
            "custom_user_access", SaaSRequestType.READ
        )

        # assert the strategy was registered
        authentication_strategies = AuthenticationStrategy.get_strategies()
        assert "custom" in [strategy.name for strategy in authentication_strategies]


class TestRegisterCustomFunctions:
    def test_function_loader(self):
        """Verify that all override implementations can be loaded by RestrictedPython"""

        overrides_path = (
            "src/fides/api/ops/service/saas_request/override_implementations"
        )

        for filename in os.listdir(overrides_path):
            if filename.endswith(".py") and filename != "__init__.py":
                file_path = os.path.join(overrides_path, filename)
                with open(file_path, "r") as file:
                    register_custom_functions(file.read())
