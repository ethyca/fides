import os
from io import BytesIO
from unittest import mock
from unittest.mock import MagicMock
from zipfile import ZipFile

import pytest

from fides.api.common_exceptions import NoSuchSaaSRequestOverrideException
from fides.api.models.custom_connector_template import CustomConnectorTemplate
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    CustomConnectorTemplateLoader,
    FileConnectorTemplateLoader,
    register_custom_functions,
)
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
)
from fides.api.util.saas_util import (
    encode_file_contents,
    load_config_from_string,
    load_yaml_as_string,
    replace_version,
)
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
    def reset_connector_template_loaders(self):
        """
        Resets the loader singleton instances before each test
        """
        FileConnectorTemplateLoader._instance = None
        CustomConnectorTemplateLoader._instance = None

    @pytest.fixture
    def zendesk_config(self) -> str:
        return load_yaml_as_string("data/saas/config/zendesk_config.yml")

    @pytest.fixture
    def zendesk_dataset(self) -> str:
        return load_yaml_as_string("data/saas/dataset/zendesk_dataset.yml")

    @pytest.fixture
    def replaceable_zendesk_config(self) -> str:
        return load_yaml_as_string(
            "tests/fixtures/saas/test_data/replaceable_zendesk_config.yml"
        )

    @pytest.fixture
    def replaceable_planet_express_config(self) -> str:
        return load_yaml_as_string(
            "tests/fixtures/saas/test_data/planet_express/replaceable_planet_express_config.yml"
        )

    @pytest.fixture
    def replaceable_zendesk_zip(
        self, replaceable_zendesk_config, zendesk_dataset
    ) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replace_version(replaceable_zendesk_config, "0.0.0"),
                "dataset.yml": zendesk_dataset,
            }
        )

    @pytest.fixture
    def non_replaceable_zendesk_zip(self, zendesk_config, zendesk_dataset) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replace_version(zendesk_config, "0.0.0"),
                "dataset.yml": zendesk_dataset,
            }
        )

    @pytest.fixture
    def replaceable_planet_express_zip(
        self,
        replaceable_planet_express_config,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
    ) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replaceable_planet_express_config,
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
                "functions.py": planet_express_functions,
            }
        )

    @pytest.fixture
    def non_replaceable_zendesk_zip(self, zendesk_config, zendesk_dataset) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replace_version(zendesk_config, "0.0.0"),
                "dataset.yml": zendesk_dataset,
            }
        )

    def test_custom_connector_template_loader_no_templates(self):
        CONFIG.security.allow_custom_connector_functions = True

        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()
        assert connector_templates == {}

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_template_loader_invalid_template(
        self,
        mock_all: MagicMock,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config="planet_express_config",
                dataset=planet_express_dataset,
                icon=planet_express_icon,
                functions=planet_express_functions,
            )
        ]

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

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_template_loader_invalid_functions(
        self,
        mock_all: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        # save custom connector template to the database
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
                functions="planet_express_functions",
            )
        ]

        # verify nothing is loaded if the custom functions fail to load
        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()
        assert connector_templates == {}

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_template_loader_custom_connector_functions_disabled(
        self,
        mock_all: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        CONFIG.security.allow_custom_connector_functions = False

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
                functions=planet_express_functions,
            )
        ]

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

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_template_loader_custom_connector_functions_disabled_custom_functions(
        self,
        mock_all: MagicMock,
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
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
                functions=None,
            )
        ]

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

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_template_loader(
        self,
        mock_all: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
                functions=planet_express_functions,
            )
        ]

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

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_loaders_have_separate_instances(
        self,
        mock_all: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
                functions=planet_express_functions,
            )
        ]

        # load custom connector templates from the database
        file_connector_templates = FileConnectorTemplateLoader.get_connector_templates()
        custom_connector_templates = (
            CustomConnectorTemplateLoader.get_connector_templates()
        )

        assert file_connector_templates != custom_connector_templates

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.create_or_update"
    )
    def test_custom_connector_save_template(
        self,
        mock_create_or_update: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
        planet_express_functions,
    ):
        db = MagicMock()

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
        assert mock_create_or_update.call_count == 2

    def test_custom_connector_template_loader_disallowed_modules(
        self,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        CONFIG.security.allow_custom_connector_functions = True

        with pytest.raises(SyntaxError) as exc:
            CustomConnectorTemplateLoader.save_template(
                MagicMock(),
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

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.delete"
    )
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_replacement_replaceable_with_update_available(
        self,
        mock_all: MagicMock,
        mock_delete: MagicMock,
        zendesk_config,
        zendesk_dataset,
    ):
        """
        Verify that an existing connector template flagged as replaceable is
        deleted when a newer version of the connector template is found in
        the FileConnectorTemplateLoader.
        """

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="zendesk",
                name="Zendesk",
                config=replace_version(zendesk_config, "0.0.0"),
                dataset=zendesk_dataset,
                replaceable=True,
            )
        ]

        template = ConnectorRegistry.get_connector_template("zendesk")
        assert template
        saas_config = load_config_from_string(template.config)
        assert (
            saas_config["version"] == load_config_from_string(zendesk_config)["version"]
        )
        assert CustomConnectorTemplateLoader.get_connector_templates() == {}
        mock_delete.assert_called_once()

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.delete"
    )
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_replacement_replaceable_with_update_not_available(
        self,
        mock_all: MagicMock,
        mock_delete: MagicMock,
        planet_express_config,
        planet_express_dataset,
    ):
        """
        Verify that an existing connector template flagged as replaceable is
        not deleted if a newer version of the connector template is not found
        in the FileConnectorTemplateLoader.
        """
        planet_express_config = replace_version(planet_express_config, "0.0.0")

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                replaceable=True,
            )
        ]

        template = ConnectorRegistry.get_connector_template("planet_express")
        assert template
        saas_config = load_config_from_string(template.config)
        assert saas_config["version"] == "0.0.0"
        assert CustomConnectorTemplateLoader.get_connector_templates() == {
            "planet_express": ConnectorTemplate(
                config=planet_express_config,
                dataset=planet_express_dataset,
                human_readable="Planet Express",
            )
        }
        mock_delete.assert_not_called()

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.delete"
    )
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_replacement_not_replaceable(
        self,
        mock_all: MagicMock,
        mock_delete: MagicMock,
        zendesk_config,
        zendesk_dataset,
    ):
        """
        Verify that an existing custom connector template flagged as not replaceable is
        not deleted even if a newer version of the connector template is found
        in the FileConnectorTemplateLoader.
        """
        zendesk_config = replace_version(zendesk_config, "0.0.0")

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="zendesk",
                name="Zendesk",
                config=zendesk_config,
                dataset=zendesk_dataset,
                replaceable=False,
            )
        ]

        template = ConnectorRegistry.get_connector_template("zendesk")
        assert template
        saas_config = load_config_from_string(template.config)
        assert saas_config["version"] == "0.0.0"
        assert CustomConnectorTemplateLoader.get_connector_templates() == {
            "zendesk": ConnectorTemplate(
                config=zendesk_config,
                dataset=zendesk_dataset,
                human_readable="Zendesk",
            )
        }
        mock_delete.assert_not_called()

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.create_or_update"
    )
    def test_replaceable_template_for_existing_template(
        self, mock_create_or_update: MagicMock, zendesk_config, replaceable_zendesk_zip
    ):
        """
        Verify that a replaceable custom connector template takes on the version of the existing connector template.
        """
        CustomConnectorTemplateLoader.save_template(
            db=MagicMock(), zip_file=ZipFile(replaceable_zendesk_zip)
        )

        assert mock_create_or_update.call_args.kwargs["data"]["replaceable"]

        config_contents = mock_create_or_update.call_args.kwargs["data"]["config"]
        custom_config = load_config_from_string(config_contents)
        existing_config = load_config_from_string(zendesk_config)
        assert custom_config["version"] == existing_config["version"]

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.create_or_update"
    )
    def test_replaceable_template_for_new_template(
        self, mock_create_or_update: MagicMock, replaceable_planet_express_zip
    ):
        """
        Verify that a replaceable custom connector template keeps its version if there is no existing connector template.
        """
        CustomConnectorTemplateLoader.save_template(
            db=MagicMock(), zip_file=ZipFile(replaceable_planet_express_zip)
        )

        assert mock_create_or_update.call_args.kwargs["data"]["replaceable"]

        config_contents = mock_create_or_update.call_args.kwargs["data"]["config"]
        custom_config = load_config_from_string(config_contents)
        assert custom_config["version"] == "0.0.1"

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.create_or_update"
    )
    def test_non_replaceable_template(
        self,
        mock_create_or_update: MagicMock,
        non_replaceable_zendesk_zip,
    ):
        """
        Verify that a non replaceable connector template keeps its version even if there is an existing connector template.
        """
        CustomConnectorTemplateLoader.save_template(
            db=MagicMock(), zip_file=ZipFile(non_replaceable_zendesk_zip)
        )
        assert not mock_create_or_update.call_args.kwargs["data"]["replaceable"]
        config_contents = mock_create_or_update.call_args.kwargs["data"]["config"]
        custom_config = load_config_from_string(config_contents)
        assert custom_config["version"] == "0.0.0"


class TestRegisterCustomFunctions:
    def test_function_loader(self):
        """Verify that all override implementations can be loaded by RestrictedPython"""

        overrides_path = "src/fides/api/service/saas_request/override_implementations"

        for filename in os.listdir(overrides_path):
            if filename.endswith(".py") and filename != "__init__.py":
                file_path = os.path.join(overrides_path, filename)
                with open(file_path, "r") as file:
                    register_custom_functions(file.read())
