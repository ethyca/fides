import os
from zipfile import ZipFile

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
from tests.ops.test_helpers.saas_test_utils import create_zip_file


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
        connector_templates = FileConnectorTemplateLoader.get_connector_templates()

        assert connector_templates.get("not_found") is None


class TestCustomConnectorTemplateLoader:
    @pytest.fixture(autouse=True)
    def reset_custom_connector_template_loader(self):
        """
        Resets the CustomConnectorTemplateLoader singleton instance before each test.
        """
        CustomConnectorTemplateLoader._instance = None

    def test_custom_connector_template_loader_no_templates(self):
        CONFIG.security.allow_custom_connector_functions = True

        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()
        assert connector_templates == {}

    def test_custom_connector_template_loader_invalid_template(
        self,
        db,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="planet_express",
            name="Planet Express",
            config="planet_express_config",
            dataset=planet_express_dataset,
            icon=planet_express_icon,
            functions=planet_express_functions,
        )
        custom_template.save(db=db)

        # verify the custom functions aren't loaded if the template is invalid
        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()
        assert connector_templates == {}

        with pytest.raises(NoSuchSaaSRequestOverrideException):
            SaaSRequestOverrideFactory.get_override(
                "planet_express_user_access", SaaSRequestType.READ
            )

        # assert the strategy was not registered
        authentication_strategies = AuthenticationStrategy.get_strategies()
        assert "planet_express" not in [
            strategy.name for strategy in authentication_strategies
        ]

    def test_custom_connector_template_loader_invalid_functions(
        self,
        db,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="planet_express",
            name="Planet Express",
            config=planet_express_config,
            dataset=planet_express_dataset,
            icon=planet_express_icon,
            functions="planet_express_functions",
        )
        custom_template.save(db=db)

        # verify nothing is loaded if the custom functions fail to load
        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()
        assert connector_templates == {}

    def test_custom_connector_template_loader_custom_connector_functions_disabled(
        self,
        db,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        CONFIG.security.allow_custom_connector_functions = False

        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="planet_express",
            name="Planet Express",
            config=planet_express_config,
            dataset=planet_express_dataset,
            icon=planet_express_icon,
            functions=planet_express_functions,
        )
        custom_template.save(db=db)

        # load custom connector templates from the database
        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()
        assert connector_templates == {}

        with pytest.raises(NoSuchSaaSRequestOverrideException):
            SaaSRequestOverrideFactory.get_override(
                "planet_express_user_access", SaaSRequestType.READ
            )

        # assert the strategy was not registered
        authentication_strategies = AuthenticationStrategy.get_strategies()
        assert "planet_express" not in [
            strategy.name for strategy in authentication_strategies
        ]

    def test_custom_connector_template_loader_custom_connector_functions_disabled_custom_functions(
        self,
        db,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        """
        A connector template with no custom functions should still be loaded
        even if allow_custom_connector_functions is set to false
        """

        CONFIG.security.allow_custom_connector_functions = False

        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="planet_express",
            name="Planet Express",
            config=planet_express_config,
            dataset=planet_express_dataset,
            icon=planet_express_icon,
            functions=None,
        )
        custom_template.save(db=db)

        # load custom connector templates from the database
        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()
        assert connector_templates == {
            "planet_express": ConnectorTemplate(
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
                human_readable="Planet Express",
            )
        }

    def test_custom_connector_template_loader(
        self,
        db,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        # save custom connector template to the database
        custom_template = CustomConnectorTemplate(
            key="planet_express",
            name="Planet Express",
            config=planet_express_config,
            dataset=planet_express_dataset,
            icon=planet_express_icon,
            functions=planet_express_functions,
        )
        custom_template.save(db=db)

        # load custom connector templates from the database
        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()

        # verify that the template in the registry is the same as the one in the database
        assert connector_templates == {
            "planet_express": ConnectorTemplate(
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
                functions=planet_express_functions,
                human_readable="Planet Express",
            )
        }

        # assert the request override was registered
        SaaSRequestOverrideFactory.get_override(
            "planet_express_user_access", SaaSRequestType.READ
        )

        # assert the strategy was registered
        authentication_strategies = AuthenticationStrategy.get_strategies()
        assert "planet_express" in [
            strategy.name for strategy in authentication_strategies
        ]

    def test_custom_connector_save_template(
        self,
        db,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        CustomConnectorTemplateLoader.save_template(
            db,
            ZipFile(
                create_zip_file(
                    {
                        "config.yml": planet_express_config,
                        "dataset.yml": planet_express_dataset,
                        "functions.py": planet_express_functions,
                        "icon.svg": planet_express_icon,
                    }
                )
            ),
        )

        # verify that a connector template can updated with no issue
        CustomConnectorTemplateLoader.save_template(
            db,
            ZipFile(
                create_zip_file(
                    {
                        "config.yml": planet_express_config,
                        "dataset.yml": planet_express_dataset,
                        "functions.py": planet_express_functions,
                        "icon.svg": planet_express_icon,
                    }
                )
            ),
        )

    def test_custom_connector_template_loader_disallowed_modules(
        self,
        db,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        with pytest.raises(SyntaxError) as exc:
            CustomConnectorTemplateLoader.save_template(
                db,
                ZipFile(
                    create_zip_file(
                        {
                            "config.yml": planet_express_config,
                            "dataset.yml": planet_express_dataset,
                            "functions.py": "import os",
                            "icon.svg": planet_express_icon,
                        }
                    )
                ),
            )
        assert "Import of 'os' module is not allowed." == str(exc.value)


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
