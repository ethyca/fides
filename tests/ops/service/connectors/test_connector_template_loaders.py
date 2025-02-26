from io import BytesIO
from unittest import mock
from unittest.mock import MagicMock
from zipfile import ZipFile

import pytest

from fides.api.common_exceptions import NoSuchSaaSRequestOverrideException
from fides.api.models.custom_connector_template import CustomConnectorTemplate
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.connector_template import ConnectorTemplate
from fides.api.service.authentication.authentication_strategy import (
    AuthenticationStrategy,
)
from fides.api.service.connectors.saas.connector_registry_service import (
    ConnectorRegistry,
    CustomConnectorTemplateLoader,
    FileConnectorTemplateLoader,
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
    def hubspot_config(self) -> str:
        return load_yaml_as_string("data/saas/config/hubspot_config.yml")

    @pytest.fixture
    def hubspot_dataset(self) -> str:
        return load_yaml_as_string("data/saas/dataset/hubspot_dataset.yml")

    @pytest.fixture
    def replaceable_hubspot_config(self) -> str:
        return load_yaml_as_string(
            "tests/fixtures/saas/test_data/replaceable_hubspot_config.yml"
        )

    @pytest.fixture
    def replaceable_planet_express_config(self) -> str:
        return load_yaml_as_string(
            "tests/fixtures/saas/test_data/planet_express/replaceable_planet_express_config.yml"
        )

    @pytest.fixture
    def replaceable_hubspot_zip(
        self, replaceable_hubspot_config, hubspot_dataset
    ) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replace_version(replaceable_hubspot_config, "0.0.0"),
                "dataset.yml": hubspot_dataset,
            }
        )

    @pytest.fixture
    def non_replaceable_hubspot_zip(self, hubspot_config, hubspot_dataset) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replace_version(hubspot_config, "0.0.0"),
                "dataset.yml": hubspot_dataset,
            }
        )

    @pytest.fixture
    def replaceable_planet_express_zip(
        self,
        replaceable_planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replaceable_planet_express_config,
                "dataset.yml": planet_express_dataset,
                "icon.svg": planet_express_icon,
            }
        )

    @pytest.fixture
    def non_replaceable_hubspot_zip(self, hubspot_config, hubspot_dataset) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replace_version(hubspot_config, "0.0.0"),
                "dataset.yml": hubspot_dataset,
            }
        )

    def test_custom_connector_template_loader_no_templates(self):
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
    ):
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config="planet_express_config",
                dataset=planet_express_dataset,
                icon=planet_express_icon,
            )
        ]

        connector_templates = CustomConnectorTemplateLoader.get_connector_templates()
        assert connector_templates == {}

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_template_loader(
        self,
        mock_all: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
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
                human_readable="Planet Express",
                authorization_required=False,
                user_guide=None,
                supported_actions=[ActionType.access],
            )
        }

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_loaders_have_separate_instances(
        self,
        mock_all: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
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
    ):
        db = MagicMock()

        CustomConnectorTemplateLoader.save_template(
            db,
            ZipFile(
                create_zip_file(
                    {
                        "config.yml": planet_express_config,
                        "dataset.yml": planet_express_dataset,
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
                        "icon.svg": planet_express_icon,
                    }
                )
            ),
        )
        assert mock_create_or_update.call_count == 2

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.create_or_update"
    )
    def test_custom_connector_save_template_with_functions(
        self,
        mock_create_or_update: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_functions,
        planet_express_icon,
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

        # assert the request override was ignored
        with pytest.raises(NoSuchSaaSRequestOverrideException) as exc:
            SaaSRequestOverrideFactory.get_override(
                "planet_express_user_access", SaaSRequestType.UPDATE
            )
        assert (
            f"Custom SaaS override 'planet_express_user_access' does not exist."
            in str(exc.value)
        )

        # assert the strategy was ignored
        authentication_strategies = AuthenticationStrategy.get_strategies()
        assert "planet_express" not in [
            strategy.name for strategy in authentication_strategies
        ]

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
        hubspot_config,
        hubspot_dataset,
    ):
        """
        Verify that an existing connector template flagged as replaceable is
        deleted when a newer version of the connector template is found in
        the FileConnectorTemplateLoader.
        """

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="hubspot",
                name="HubSpot",
                config=replace_version(hubspot_config, "0.0.0"),
                dataset=hubspot_dataset,
                replaceable=True,
            )
        ]

        template = ConnectorRegistry.get_connector_template("hubspot")
        assert template
        saas_config = load_config_from_string(template.config)
        assert (
            saas_config["version"] == load_config_from_string(hubspot_config)["version"]
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
                authorization_required=False,
                user_guide=None,
                supported_actions=[ActionType.access],
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
        hubspot_config,
        hubspot_dataset,
    ):
        """
        Verify that an existing custom connector template flagged as not replaceable is
        not deleted even if a newer version of the connector template is found
        in the FileConnectorTemplateLoader.
        """
        hubspot_config = replace_version(hubspot_config, "0.0.0")

        mock_all.return_value = [
            CustomConnectorTemplate(
                key="hubspot",
                name="HubSpot",
                config=hubspot_config,
                dataset=hubspot_dataset,
                replaceable=False,
            )
        ]

        template = ConnectorRegistry.get_connector_template("hubspot")
        assert template
        saas_config = load_config_from_string(template.config)
        assert saas_config["version"] == "0.0.0"
        assert CustomConnectorTemplateLoader.get_connector_templates() == {
            "hubspot": ConnectorTemplate(
                config=hubspot_config,
                dataset=hubspot_dataset,
                human_readable="HubSpot",
                authorization_required=False,
                user_guide="https://docs.ethyca.com/user-guides/integrations/saas-integrations/hubspot",
                supported_actions=[ActionType.access, ActionType.erasure],
            )
        }
        mock_delete.assert_not_called()

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.create_or_update"
    )
    def test_replaceable_template_for_existing_template(
        self, mock_create_or_update: MagicMock, hubspot_config, replaceable_hubspot_zip
    ):
        """
        Verify that a replaceable custom connector template takes on the version of the existing connector template.
        """
        CustomConnectorTemplateLoader.save_template(
            db=MagicMock(), zip_file=ZipFile(replaceable_hubspot_zip)
        )

        assert mock_create_or_update.call_args.kwargs["data"]["replaceable"]

        config_contents = mock_create_or_update.call_args.kwargs["data"]["config"]
        custom_config = load_config_from_string(config_contents)
        existing_config = load_config_from_string(hubspot_config)
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
        non_replaceable_hubspot_zip,
    ):
        """
        Verify that a non replaceable connector template keeps its version even if there is an existing connector template.
        """
        CustomConnectorTemplateLoader.save_template(
            db=MagicMock(), zip_file=ZipFile(non_replaceable_hubspot_zip)
        )
        assert not mock_create_or_update.call_args.kwargs["data"]["replaceable"]
        config_contents = mock_create_or_update.call_args.kwargs["data"]["config"]
        custom_config = load_config_from_string(config_contents)
        assert custom_config["version"] == "0.0.0"
