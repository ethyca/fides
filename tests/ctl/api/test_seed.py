from json import dumps
from typing import Generator

import pytest
from fideslang import DEFAULT_TAXONOMY, DataCategory
from starlette.testclient import TestClient

from fides.api.ctl.database import seed
from fides.ctl.core.api import generate_resource_url
from fides.ctl.core.config import FidesConfig


@pytest.fixture(scope="function", name="data_category")
def fixture_data_category(
    test_config: FidesConfig, test_client: TestClient
) -> Generator:
    """
    Fixture that yields a data category and then deletes it for each test run.
    """
    fides_key = "foo"
    yield DataCategory(fides_key=fides_key, parent_key=None)

    test_client.delete(
        generate_resource_url(
            test_config.cli.server_url, "data_category", resource_id=fides_key
        ),
        headers=test_config.user.request_headers,
    )


@pytest.mark.unit
class TestFilterDataCategories:
    def test_filter_data_categories_excluded(self) -> None:
        """Test that the filter method works as intended"""
        excluded_data_categories = [
            "user.financial",
            "user.payment",
            "user.credentials",
        ]
        all_data_categories = [
            "user.name",
            "user.test",
            # These should be excluded
            "user.payment",
            "user.payment.financial_account_number",
            "user.credentials",
            "user.credentials.biometric_credentials",
            "user.financial.account_number",
            "user.financial",
        ]
        expected_result = [
            "user.name",
            "user.test",
        ]
        assert seed.filter_data_categories(
            all_data_categories, excluded_data_categories
        ) == sorted(expected_result)

    def test_filter_data_categories_no_third_level(self) -> None:
        """Test that the filter method works as intended"""
        excluded_data_categories = [
            "user.financial",
            "user.payment",
            "user.credentials",
        ]
        all_data_categories = [
            "user.name",
            "user.test",
            # These should be excluded
            "user.payment",
            "user.payment.financial_account_number",
            "user.credentials",
            "user.credentials.biometric_credentials",
            "user.financial.account_number",
            "user.financial",
        ]
        expected_result = [
            "user.name",
            "user.test",
        ]
        assert seed.filter_data_categories(
            all_data_categories, excluded_data_categories
        ) == sorted(expected_result)

    def test_filter_data_categories_no_top_level(self) -> None:
        """Test that the filter method works as intended"""
        all_data_categories = [
            "user",
            "user.name",
            "user.test",
        ]
        expected_result = [
            "user.name",
            "user.test",
        ]
        assert seed.filter_data_categories(all_data_categories, []) == expected_result

    def test_filter_data_categories_empty_excluded(self) -> None:
        """Test that the filter method works as intended"""
        all_data_categories = [
            "user.name",
            "user.payment",
            "user.credentials",
            "user.financial",
        ]
        assert seed.filter_data_categories(all_data_categories, []) == sorted(
            all_data_categories
        )

    def test_filter_data_categories_no_exclusions(self) -> None:
        """Test that the filter method works as intended"""
        excluded_data_categories = ["user.payment"]
        all_data_categories = [
            "user.name",
            "user.credentials",
            "user.financial",
        ]
        assert seed.filter_data_categories(
            all_data_categories, excluded_data_categories
        ) == sorted(all_data_categories)

    def test_filter_data_categories_only_return_users(self) -> None:
        """Test that the filter method works as intended"""
        all_data_categories = [
            "user.name",
            "user.credentials",
            "user.financial",
            # These are excluded
            "nonuser.foo",
            "anotheruser.foo",
        ]
        expected_categories = [
            "user.name",
            "user.credentials",
            "user.financial",
        ]
        assert seed.filter_data_categories(all_data_categories, []) == sorted(
            expected_categories
        )


@pytest.mark.integration
class TestLoadDefaultTaxonomy:
    """Tests related to load_default_taxonomy"""

    async def test_add_to_default_taxonomy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        test_config: FidesConfig,
        data_category: DataCategory,
        test_client,
        async_session,
    ) -> None:
        """Should be able to add to the existing default taxonomy"""
        result = test_client.get(
            generate_resource_url(
                test_config.cli.server_url,
                resource_type="data_category",
                resource_id=data_category.fides_key,
            ),
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 404

        updated_default_taxonomy = DEFAULT_TAXONOMY.copy()
        updated_default_taxonomy.data_category.append(data_category)

        monkeypatch.setattr(seed, "DEFAULT_TAXONOMY", updated_default_taxonomy)
        await seed.load_default_resources(async_session)

        result = test_client.get(
            generate_resource_url(
                test_config.cli.server_url,
                resource_type="data_category",
                resource_id=data_category.fides_key,
            ),
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 200

    async def test_does_not_override_user_changes(
        self, test_config: FidesConfig, test_client, async_session
    ) -> None:
        """
        Loading the default taxonomy should not override user changes
        to their default taxonomy
        """
        default_category = DEFAULT_TAXONOMY.data_category[0].copy()
        new_description = "foo description"
        default_category.description = new_description

        result = test_client.put(
            generate_resource_url(test_config.cli.server_url, "data_category"),
            headers=test_config.user.request_headers,
            data=default_category.json(),
        )

        assert result.status_code == 200

        await seed.load_default_resources(async_session)

        result = test_client.get(
            generate_resource_url(
                test_config.cli.server_url,
                resource_type="data_category",
                resource_id=default_category.fides_key,
            ),
            headers=test_config.user.request_headers,
        )
        assert result.json()["description"] == new_description

    async def test_does_not_remove_user_added_taxonomies(
        self,
        test_config: FidesConfig,
        data_category: DataCategory,
        test_client,
        async_session,
    ) -> None:
        """
        Loading the default taxonomy should not delete user additions
        to their default taxonomy
        """
        test_client.post(
            generate_resource_url(test_config.cli.server_url, "data_category"),
            headers=test_config.user.request_headers,
            data=data_category.json(),
        )

        await seed.load_default_resources(async_session)

        result = test_client.get(
            generate_resource_url(
                test_config.cli.server_url,
                resource_type="data_category",
                resource_id=data_category.fides_key,
            ),
            headers=test_config.user.request_headers,
        )
        assert result.status_code == 200
