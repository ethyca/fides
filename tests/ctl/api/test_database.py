from typing import Generator

import pytest
from fideslang import DEFAULT_TAXONOMY, DataCategory

from fides.api.ctl.database import database
from fides.ctl.core import api as _api
from fides.ctl.core.config import FidesctlConfig


@pytest.fixture(scope="function", name="data_category")
def fixture_data_category(test_config: FidesctlConfig) -> Generator:
    """
    Fixture that yields a data category and then deletes it for each test run.
    """
    fides_key = "foo"
    yield DataCategory(fides_key=fides_key, parent_key=None)

    _api.delete(
        url=test_config.cli.server_url,
        resource_type="data_category",
        resource_id=fides_key,
        headers=test_config.user.request_headers,
    )


@pytest.mark.integration
class TestLoadDefaultTaxonomy:
    """Tests related to load_default_taxonomy"""

    async def test_add_to_default_taxonomy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        test_config: FidesctlConfig,
        data_category: DataCategory,
    ) -> None:
        """Should be able to add to the existing default taxonomy"""
        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 404

        updated_default_taxonomy = DEFAULT_TAXONOMY.copy()
        updated_default_taxonomy.data_category.append(data_category)

        monkeypatch.setattr(database, "DEFAULT_TAXONOMY", updated_default_taxonomy)
        await database.load_default_taxonomy()

        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 200

    async def test_does_not_override_user_changes(
        self, test_config: FidesctlConfig
    ) -> None:
        """
        Loading the default taxonomy should not override user changes
        to their default taxonomy
        """
        default_category = DEFAULT_TAXONOMY.data_category[0].copy()
        new_description = "foo description"
        default_category.description = new_description
        result = _api.update(
            test_config.cli.server_url,
            "data_category",
            json_resource=default_category.json(),
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 200

        await database.load_default_taxonomy()
        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            default_category.fides_key,
            headers=test_config.user.request_headers,
        )
        assert result.json()["description"] == new_description

    async def test_does_not_remove_user_added_taxonomies(
        self, test_config: FidesctlConfig, data_category: DataCategory
    ) -> None:
        """
        Loading the default taxonomy should not delete user additions
        to their default taxonomy
        """
        result = _api.create(
            test_config.cli.server_url,
            "data_category",
            json_resource=data_category.json(),
            headers=test_config.user.request_headers,
        )

        await database.load_default_taxonomy()

        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 200
