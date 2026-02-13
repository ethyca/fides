from datetime import datetime, timezone
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
    @pytest.fixture(scope="function", autouse=True)
    def reset_connector_template_loaders(self):
        """
        Resets the loader singleton instances and the db_timestamp_cached
        decorator cache before each test so tests don't bleed into each other.
        """
        FileConnectorTemplateLoader._instance = None
        CustomConnectorTemplateLoader._instance = None
        CustomConnectorTemplateLoader.get_connector_templates.cache_clear()  # type: ignore[attr-defined]

    @pytest.fixture
    def hubspot_config(self) -> str:
        return load_yaml_as_string("data/saas/config/hubspot_config.yml")

    @pytest.fixture
    def hubspot_dataset(self) -> str:
        return load_yaml_as_string("data/saas/dataset/hubspot_dataset.yml")

    @pytest.fixture
    def custom_hubspot_config(self) -> str:
        return load_yaml_as_string(
            "tests/fixtures/saas/test_data/replaceable_hubspot_config.yml"
        )

    @pytest.fixture
    def custom_hubspot_zip(self, custom_hubspot_config, hubspot_dataset) -> BytesIO:
        return create_zip_file(
            {
                "config.yml": replace_version(custom_hubspot_config, "0.0.0"),
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
                custom=True,
                default_connector_available=False,
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

        connector_type = CustomConnectorTemplateLoader.save_template(
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
        assert connector_type == "planet_express"
        assert mock_create_or_update.call_count == 1

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
            "Custom SaaS override 'planet_express_user_access' does not exist."
            in str(exc.value)
        )

        # assert the strategy was ignored
        authentication_strategies = AuthenticationStrategy.get_strategies()
        assert "planet_express" not in [
            strategy.name for strategy in authentication_strategies
        ]

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_custom_connector_replaces_file_connector(
        self,
        mock_all: MagicMock,
        hubspot_config,
        hubspot_dataset,
    ):
        """
        Verify that a custom connector template replaces the file connector template
        when it is loaded, and that it has custom=True and default_connector_available=True.
        """
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="hubspot",
                name="HubSpot",
                config=replace_version(hubspot_config, "0.0.0"),
                dataset=hubspot_dataset,
            )
        ]

        template = ConnectorRegistry.get_connector_template("hubspot")
        assert template
        saas_config = load_config_from_string(template.config)
        assert saas_config["version"] == "0.0.0"
        assert template.custom is True
        assert template.default_connector_available is True

    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.create_or_update"
    )
    def test_version_update_for_custom_connector(
        self, mock_create_or_update: MagicMock, hubspot_config, custom_hubspot_zip
    ):
        """
        Verify that a custom connector template takes on the version of the existing file connector template.
        """
        CustomConnectorTemplateLoader.save_template(
            db=MagicMock(), zip_file=ZipFile(custom_hubspot_zip)
        )

        config_contents = mock_create_or_update.call_args.kwargs["data"]["config"]
        custom_config = load_config_from_string(config_contents)
        existing_config = load_config_from_string(hubspot_config)
        assert custom_config["version"] == existing_config["version"]


class TestCustomConnectorTemplateLoaderCaching:
    """Tests that the db_timestamp_cached decorator works correctly when
    integrated with CustomConnectorTemplateLoader and ConnectorRegistry.

    All tests mock _get_table_state to control the DB fingerprint and
    CustomConnectorTemplate.all to control the loaded data, so no real
    DB session is needed.
    """

    @pytest.fixture(scope="function", autouse=True)
    def reset_loaders_and_cache(self):
        """Reset singletons and the decorator cache before each test."""
        FileConnectorTemplateLoader._instance = None
        CustomConnectorTemplateLoader._instance = None
        CustomConnectorTemplateLoader.get_connector_templates.cache_clear()  # type: ignore[attr-defined]

    @mock.patch("fides.api.util.db_timestamp_cache._get_table_state")
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_unchanged_db_state_returns_cached_result_without_reloading(
        self,
        mock_all: MagicMock,
        mock_table_state: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        """When the DB fingerprint is unchanged between calls,
        get_connector_templates should return the cached dict and NOT
        call CustomConnectorTemplate.all a second time."""
        t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_table_state.return_value = (t1, 1)
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
            )
        ]

        first = CustomConnectorTemplateLoader.get_connector_templates()
        second = CustomConnectorTemplateLoader.get_connector_templates()

        assert "planet_express" in first
        assert first == second
        # all() should only be called once; the second call is a cache hit
        assert mock_all.call_count == 1

    @mock.patch("fides.api.util.db_timestamp_cache._get_table_state")
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_db_state_change_triggers_reload(
        self,
        mock_all: MagicMock,
        mock_table_state: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        """When the DB fingerprint changes (updated_at advances), the
        cached result must be discarded and the function re-invoked."""
        t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 1, 2, tzinfo=timezone.utc)

        mock_table_state.return_value = (t1, 1)
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
            )
        ]

        first = CustomConnectorTemplateLoader.get_connector_templates()
        assert "planet_express" in first

        # Simulate a DB change: updated_at advances
        mock_table_state.return_value = (t2, 1)
        mock_all.return_value = []  # templates were cleared

        second = CustomConnectorTemplateLoader.get_connector_templates()
        assert second == {}
        assert mock_all.call_count == 2

    @mock.patch("fides.api.util.db_timestamp_cache._get_table_state")
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_row_deletion_detected_by_count_change(
        self,
        mock_all: MagicMock,
        mock_table_state: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        """A row deletion that doesn't change MAX(updated_at) must still
        invalidate the cache because COUNT(*) decreases."""
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_table_state.return_value = (now, 1)
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
            )
        ]

        first = CustomConnectorTemplateLoader.get_connector_templates()
        assert "planet_express" in first

        # Count drops (row deleted) but max_updated_at unchanged
        mock_table_state.return_value = (now, 0)
        mock_all.return_value = []

        second = CustomConnectorTemplateLoader.get_connector_templates()
        assert second == {}
        assert mock_all.call_count == 2

    @mock.patch("fides.api.util.db_timestamp_cache._get_table_state")
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_save_template_invalidates_cache(
        self,
        mock_all: MagicMock,
        mock_table_state: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        """After save_template() the cache must be cleared so that the
        next get_connector_templates() call reloads from the DB."""
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_table_state.return_value = (now, 0)
        mock_all.return_value = []

        # Populate cache with empty result
        assert CustomConnectorTemplateLoader.get_connector_templates() == {}
        assert mock_all.call_count == 1

        # save_template clears cache; simulate the DB now having a record
        with mock.patch(
            "fides.api.models.custom_connector_template.CustomConnectorTemplate.create_or_update"
        ):
            CustomConnectorTemplateLoader.save_template(
                db=MagicMock(),
                zip_file=ZipFile(
                    create_zip_file(
                        {
                            "config.yml": planet_express_config,
                            "dataset.yml": planet_express_dataset,
                            "icon.svg": planet_express_icon,
                        }
                    )
                ),
            )

        # DB state has changed after the save
        mock_table_state.return_value = (now, 1)
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
            )
        ]

        result = CustomConnectorTemplateLoader.get_connector_templates()
        assert "planet_express" in result
        # all() called again because save_template cleared the cache
        assert mock_all.call_count >= 2

    @mock.patch("fides.api.util.db_timestamp_cache._get_table_state")
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_delete_template_invalidates_cache(
        self,
        mock_all: MagicMock,
        mock_table_state: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        """After delete_template() the cache must be cleared so the
        deleted template no longer appears."""
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_table_state.return_value = (now, 1)
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
            )
        ]

        assert (
            "planet_express" in CustomConnectorTemplateLoader.get_connector_templates()
        )

        # delete_template clears cache
        with mock.patch(
            "fides.api.models.custom_connector_template.CustomConnectorTemplate.filter"
        ) as mock_filter:
            mock_filter.return_value.delete.return_value = None
            CustomConnectorTemplateLoader.delete_template(MagicMock(), "planet_express")

        # DB state now reflects deletion
        mock_table_state.return_value = (now, 0)
        mock_all.return_value = []

        result = CustomConnectorTemplateLoader.get_connector_templates()
        assert result == {}

    @mock.patch("fides.api.util.db_timestamp_cache._get_table_state")
    @mock.patch(
        "fides.api.models.custom_connector_template.CustomConnectorTemplate.all"
    )
    def test_connector_registry_uses_cached_custom_templates(
        self,
        mock_all: MagicMock,
        mock_table_state: MagicMock,
        planet_express_config,
        planet_express_dataset,
        planet_express_icon,
    ):
        """ConnectorRegistry._get_combined_templates should benefit from
        the cache: repeated calls with unchanged DB state should not
        trigger additional loads of custom templates."""
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_table_state.return_value = (now, 1)
        mock_all.return_value = [
            CustomConnectorTemplate(
                key="planet_express",
                name="Planet Express",
                config=planet_express_config,
                dataset=planet_express_dataset,
                icon=planet_express_icon,
            )
        ]

        # Two consecutive calls through the registry
        first = ConnectorRegistry.get_connector_template("planet_express")
        second = ConnectorRegistry.get_connector_template("planet_express")

        assert first is not None
        assert first == second
        # CustomConnectorTemplate.all should only be called once
        assert mock_all.call_count == 1
