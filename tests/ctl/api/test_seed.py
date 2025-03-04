import io
import os
from textwrap import dedent
from typing import Generator
from unittest.mock import patch

import pytest
from fideslang.default_taxonomy import DEFAULT_TAXONOMY
from fideslang.models import DataCategory, Organization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fides.api.db import samples, seed
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.datasetconfig import DatasetConfig
from fides.api.models.fides_user import FidesUser
from fides.api.models.policy import ActionType, DrpAction, Policy, Rule, RuleTarget
from fides.api.models.sql_models import Dataset, PolicyCtl, System
from fides.api.util.data_category import filter_data_categories
from fides.config import CONFIG, FidesConfig
from fides.core import api as _api


@pytest.fixture(scope="function", name="data_category")
def fixture_data_category(test_config: FidesConfig) -> Generator:
    """
    Fixture that yields a data category and then deletes it for each test run.
    """
    fides_key = "foo"
    yield DataCategory(fides_key=fides_key, parent_key=None)

    _api.delete(
        url=test_config.cli.server_url,
        resource_type="data_category",
        resource_id=fides_key,
        headers=CONFIG.user.auth_header,
    )


@pytest.fixture
def parent_server_config():
    original_username = CONFIG.security.parent_server_username
    original_password = CONFIG.security.parent_server_password
    CONFIG.security.parent_server_username = "test_user"
    CONFIG.security.parent_server_password = "Atestpassword1!"
    yield
    CONFIG.security.parent_server_username = original_username
    CONFIG.security.parent_server_password = original_password


@pytest.fixture
def parent_server_config_none():
    original_username = CONFIG.security.parent_server_username
    original_password = CONFIG.security.parent_server_password
    CONFIG.security.parent_server_username = None
    CONFIG.security.parent_server_password = None
    yield
    CONFIG.security.parent_server_username = original_username
    CONFIG.security.parent_server_password = original_password


@pytest.fixture
def parent_server_config_username_only():
    original_username = CONFIG.security.parent_server_username
    original_password = CONFIG.security.parent_server_password
    CONFIG.security.parent_server_username = "test_user"
    CONFIG.security.parent_server_password = None
    yield
    CONFIG.security.parent_server_username = original_username
    CONFIG.security.parent_server_password = original_password


@pytest.fixture
def parent_server_config_password_only():
    original_username = CONFIG.security.parent_server_username
    original_password = CONFIG.security.parent_server_password
    CONFIG.security.parent_server_username = None
    CONFIG.security.parent_server_password = "Atestpassword1!"
    yield
    CONFIG.security.parent_server_username = original_username
    CONFIG.security.parent_server_password = original_password


@pytest.mark.unit
class TestFilterDataCategories:
    @pytest.mark.skip("this times out on CI")
    def test_filter_data_categories_excluded(self) -> None:
        """Test that the filter method works as intended"""
        excluded_data_categories = [
            "user.financial",
            "user.payment",
            "user.authorization",
        ]
        all_data_categories = [
            "user.name",
            "user.test",
            # These should be excluded
            "user.payment",
            "user.payment.financial_account_number",
            "user.authorization.credentials",
            "user.authorization.biometric",
            "user.financial.bank_account",
            "user.financial",
        ]
        expected_result = [
            "user.name",
            "user.test",
        ]
        assert filter_data_categories(
            all_data_categories, excluded_data_categories
        ) == sorted(expected_result)

    def test_filter_data_categories_no_third_level(self) -> None:
        """Test that the filter method works as intended"""
        excluded_data_categories = [
            "user.financial",
            "user.payment",
            "user.authorization",
        ]
        all_data_categories = [
            "user.name",
            "user.test",
            # These should be excluded
            "user.payment",
            "user.payment.financial_account_number",
            "user.authorization.credentials",
            "user.authorization.biometric",
            "user.financial.bank_account",
            "user.financial",
        ]
        expected_result = [
            "user.name",
            "user.test",
        ]
        assert filter_data_categories(
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
        assert filter_data_categories(all_data_categories, []) == expected_result

    def test_filter_data_categories_empty_excluded(self) -> None:
        """Test that the filter method works as intended"""
        all_data_categories = [
            "user.name",
            "user.payment",
            "user.authorization",
            "user.financial",
        ]
        assert filter_data_categories(all_data_categories, []) == sorted(
            all_data_categories
        )

    def test_filter_data_categories_no_exclusions(self) -> None:
        """Test that the filter method works as intended"""
        excluded_data_categories = ["user.payment"]
        all_data_categories = [
            "user.name",
            "user.authorization",
            "user.financial",
        ]
        assert filter_data_categories(
            all_data_categories, excluded_data_categories
        ) == sorted(all_data_categories)

    def test_filter_data_categories_only_return_users(self) -> None:
        """Test that the filter method works as intended"""
        all_data_categories = [
            "user.name",
            "user.authorization",
            "user.financial",
            # These are excluded
            "nonuser.foo",
            "anotheruser.foo",
        ]
        expected_categories = [
            "user.name",
            "user.authorization",
            "user.financial",
        ]
        assert filter_data_categories(all_data_categories, []) == sorted(
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
        async_session: AsyncSession,
    ) -> None:
        """Should be able to add to the existing default taxonomy"""
        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=CONFIG.user.auth_header,
        )
        assert result.status_code == 404

        updated_default_taxonomy = DEFAULT_TAXONOMY.model_copy()
        updated_default_taxonomy.data_category.append(data_category)

        monkeypatch.setattr(seed, "DEFAULT_TAXONOMY", updated_default_taxonomy)
        await seed.load_default_resources(async_session)

        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=CONFIG.user.auth_header,
        )
        assert result.status_code == 200

    async def test_does_not_override_user_changes(
        self, test_config: FidesConfig, async_session: AsyncSession
    ) -> None:
        """
        Loading the default taxonomy should not override user changes
        to their default taxonomy
        """
        default_category = DEFAULT_TAXONOMY.data_category[0].model_copy()
        new_description = "foo description"
        default_category.description = new_description
        result = _api.update(
            test_config.cli.server_url,
            "data_category",
            json_resource=default_category.json(),
            headers=CONFIG.user.auth_header,
        )
        assert result.status_code == 200

        await seed.load_default_resources(async_session)
        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            default_category.fides_key,
            headers=CONFIG.user.auth_header,
        )
        assert result.json()["description"] == new_description

    async def test_does_not_remove_user_added_taxonomies(
        self,
        test_config: FidesConfig,
        data_category: DataCategory,
        async_session: AsyncSession,
    ) -> None:
        """
        Loading the default taxonomy should not delete user additions
        to their default taxonomy
        """
        _api.create(
            test_config.cli.server_url,
            "data_category",
            json_resource=data_category.json(),
            headers=CONFIG.user.auth_header,
        )

        await seed.load_default_resources(async_session)

        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=CONFIG.user.auth_header,
        )
        assert result.status_code == 200


@pytest.mark.usefixtures("parent_server_config")
def test_create_or_update_parent_user(db):
    seed.create_or_update_parent_user()
    user = FidesUser.get_by(
        db, field="username", value=CONFIG.security.parent_server_username
    )

    assert user is not None
    user.delete(db)


@pytest.mark.usefixtures("parent_server_config")
def test_create_or_update_parent_user_called_twice(db):
    """
    Ensure seed method can be called twice with same parent user config,
    since this is effectively what happens on server restart.
    """
    seed.create_or_update_parent_user()
    user = FidesUser.get_by(
        db, field="username", value=CONFIG.security.parent_server_username
    )

    assert user is not None

    seed.create_or_update_parent_user()
    user = FidesUser.get_by(
        db, field="username", value=CONFIG.security.parent_server_username
    )

    assert user is not None
    user.delete(db)


@pytest.mark.usefixtures("parent_server_config")
def test_create_or_update_parent_user_change_password(db):
    user = FidesUser.create(
        db=db,
        data={
            "username": CONFIG.security.parent_server_username,
            "password": "Somepassword1!",
        },
    )

    seed.create_or_update_parent_user()
    db.refresh(user)

    assert user.password_reset_at is not None
    assert user.credentials_valid(CONFIG.security.parent_server_password) is True
    user.delete(db)


@pytest.mark.usefixtures("parent_server_config_none")
def test_create_or_update_parent_user_no_settings(db):
    seed.create_or_update_parent_user()
    user = FidesUser.all(db)

    assert user == []


@pytest.mark.usefixtures("parent_server_config_username_only")
def test_create_or_update_parent_user_username_only():
    with pytest.raises(ValueError):
        seed.create_or_update_parent_user()


@pytest.mark.usefixtures("parent_server_config_password_only")
def test_create_or_update_parent_user_password_only():
    with pytest.raises(ValueError):
        seed.create_or_update_parent_user()


async def test_load_default_dsr_policies(
    db,
):
    # seed the default dsr policies and its artifacts
    seed.load_default_dsr_policies()

    # run some basic checks on its artifacts to make sure they're populated as we expect
    access_policy: Policy = Policy.get_by(
        db, field="key", value=seed.DEFAULT_ACCESS_POLICY
    )
    assert access_policy.name == "Default Access Policy"
    assert len(access_policy.rules) == 1

    access_rule: Rule = access_policy.rules[0]
    assert access_rule.key == seed.DEFAULT_ACCESS_POLICY_RULE
    assert access_rule.name == "Default Access Rule"
    assert access_rule.action_type == ActionType.access.value

    assert len(access_rule.targets) >= 1

    erasure_policy: Policy = Policy.get_by(
        db, field="key", value=seed.DEFAULT_ERASURE_POLICY
    )
    assert erasure_policy.name == "Default Erasure Policy"
    assert len(erasure_policy.rules) == 1

    erasure_rule: Rule = erasure_policy.rules[0]
    assert erasure_rule.key == seed.DEFAULT_ERASURE_POLICY_RULE
    assert erasure_rule.name == "Default Erasure Rule"
    assert erasure_rule.action_type == ActionType.erasure.value

    # make some manual changes to the artifacts to test that they will not
    # be overwritten when we re-run the seed function
    Policy.create_or_update(
        db,
        data={
            "name": "-- changed policy name --",
            "key": seed.DEFAULT_ACCESS_POLICY,
            "execution_timeframe": 45,
            "drp_action": DrpAction.access.value,
        },
    )

    Rule.create_or_update(
        db=db,
        data={
            "action_type": ActionType.access.value,
            "name": "-- changed access rule name --",
            "key": seed.DEFAULT_ACCESS_POLICY_RULE,
            "policy_id": access_policy.id,
        },
    )

    num_rule_targets = len(access_rule.targets)
    rule_target: RuleTarget = access_rule.targets[0]
    rule_target.delete(db)

    assert RuleTarget.get_by(db, field="key", value=rule_target.key) is None
    db.refresh(access_rule)
    assert len(access_rule.targets) == num_rule_targets - 1

    # now test that re-running `load_default_dsr_policies()` does not
    # overwrite any of the manual changed that have been made to the artifacts

    seed.load_default_dsr_policies()

    access_policy: Policy = Policy.get_by(
        db, field="key", value=seed.DEFAULT_ACCESS_POLICY
    )
    db.refresh(access_policy)
    assert access_policy.name == "-- changed policy name --"
    assert len(access_policy.rules) == 1

    access_rule: Rule = access_policy.rules[0]
    db.refresh(access_policy)
    assert access_rule.key == seed.DEFAULT_ACCESS_POLICY_RULE
    assert access_rule.name == "-- changed access rule name --"
    assert access_rule.action_type == ActionType.access.value

    assert len(access_rule.targets) == num_rule_targets - 1


async def test_load_organizations(loguru_caplog, async_session, monkeypatch):
    updated_default_taxonomy = DEFAULT_TAXONOMY.model_copy()
    current_orgs = len(updated_default_taxonomy.organization)
    updated_default_taxonomy.organization.append(
        Organization(fides_key="new_organization")
    )

    monkeypatch.setattr(seed, "DEFAULT_TAXONOMY", updated_default_taxonomy)
    await seed.load_default_organization(async_session)

    assert "INSERTED 1" in loguru_caplog.text
    assert f"SKIPPED {current_orgs}" in loguru_caplog.text


@pytest.mark.integration
class TestLoadSamples:
    """Tests related to load_samples"""

    SAMPLE_ENV_VARS = {
        # Include test secrets for Postgres, Mongo, and Stripe, only
        "FIDES_DEPLOY__CONNECTORS__POSTGRES__HOST": "test-var-expansion",
        "FIDES_DEPLOY__CONNECTORS__POSTGRES__PORT": "9090",
        "FIDES_DEPLOY__CONNECTORS__POSTGRES__DBNAME": "test-var-db",
        "FIDES_DEPLOY__CONNECTORS__POSTGRES__USERNAME": "test-var-user",
        "FIDES_DEPLOY__CONNECTORS__POSTGRES__PASSWORD": "test-var-password",
        "FIDES_DEPLOY__CONNECTORS__POSTGRES__SSH_REQUIRED": "false",
        "FIDES_DEPLOY__CONNECTORS__STRIPE__DOMAIN": "test-stripe-domain",
        "FIDES_DEPLOY__CONNECTORS__STRIPE__API_KEY": "test-stripe-api-key",
        "FIDES_DEPLOY__CONNECTORS__MONGO_HOST": "test-var-expansion",
        "FIDES_DEPLOY__CONNECTORS__MONGO_PORT": "9090",
        "FIDES_DEPLOY__CONNECTORS__MONGO_DEFAULTAUTHDB": "test-var-db",
        "FIDES_DEPLOY__CONNECTORS__MONGO_USERNAME": "test-var-user",
        "FIDES_DEPLOY__CONNECTORS__MONGO_PASSWORD": "test-var-password",
    }

    @patch.dict(os.environ, SAMPLE_ENV_VARS, clear=True)
    async def test_load_samples(
        self,
        async_session: AsyncSession,
    ) -> None:
        """
        Test that we can load the sample resources, connections, and upsert those
        into the database. See the other tests in this class for more detailed
        assertions - this one just ensures the e2e result is what we expect: a
        database full of sample data!
        """

        # Load the sample resources & connections
        await seed.load_samples(async_session)

        async with async_session.begin():
            # Check the results are as expected!
            systems = (await async_session.execute(select(System))).scalars().all()
            datasets = (await async_session.execute(select(Dataset))).scalars().all()
            policies = (await async_session.execute(select(PolicyCtl))).scalars().all()
            connections = (
                (await async_session.execute(select(ConnectionConfig))).scalars().all()
            )
            dataset_configs = (
                (await async_session.execute(select(DatasetConfig))).scalars().all()
            )
            assert len(systems) == 6
            assert len(datasets) == 5
            assert len(policies) == 1
            assert len(connections) == 4
            assert len(dataset_configs) == 4

            assert sorted([e.fides_key for e in systems]) == [
                "cookie_house",
                "cookie_house_custom_request_fields_database",
                "cookie_house_customer_database",
                "cookie_house_loyalty_database",
                "cookie_house_marketing_system",
                "cookie_house_postgresql_database",
            ]
            assert sorted([e.fides_key for e in datasets]) == [
                "mongo_test",
                "postgres_example_custom_request_field_dataset",
                "postgres_example_test_dataset",
                "postgres_example_test_extended_dataset",
                "stripe_connector",
            ]
            assert sorted([e.fides_key for e in policies]) == ["sample_policy"]

            # NOTE: Only the connections configured by SAMPLE_ENV_VARS above are
            # expected to exist; the others defined in the sample_connections.yml
            # will be ignored since they are missing secrets!
            assert sorted([e.key for e in connections]) == [
                "cookie_house_custom_request_fields_database",
                "cookie_house_customer_database_mongodb",
                "cookie_house_postgresql_database",
                "stripe_connector",
            ]
            assert sorted([e.fides_key for e in dataset_configs]) == [
                "mongo_test",
                "postgres_example_custom_request_field_dataset",
                "postgres_example_test_dataset",
                "stripe_connector",
            ]

    async def test_load_sample_resources(self):
        """
        Ensure that the resource files in the sample project are all
        successfully parsed by the load_sample_resources_from_project()
        function. This makes sure we don't make some changes to the sample
        project files that aren't automatically loaded into the database via
        this function.

        NOTE: If you've found this test, that probably means you were making
        some changes to the code and this failed unexpectedly. Maybe you removed
        a field, changed a default, or wanted to edit some sample data?

        To fix the test, you just need to ensure the code has all the logic it
        needs to parse everything from this directory:
        - src/fides/data/sample_project/sample_resources/*.yml

        See src/fides/api/database/samples.py for details.

        Sorry for the trouble, but we want to ensure there isn't a subtle bug
        sneaking into our sample project code!
        """
        error_message = (
            "Unexpected error loading sample resources; did you make changes to the sample project? "
            "See tests/ctl/api/test_seed.py for details."
        )
        try:
            samples.load_sample_resources_from_project()
            assert True
        except Exception as exc:
            print(exc)
            assert False, error_message

    @patch.dict(os.environ, SAMPLE_ENV_VARS, clear=True)
    async def test_load_sample_connections(self):
        """
        Ensure that the sample connections file in the sample project can be
        parsed and loaded by the load_sample_connections_from_project() function.
        This makes sure we don't make some changes to the sample project files
        that aren't automatically loaded into the database via this function.

        NOTE: If you've found this test, that probably means you were making
        some changes to the code and this failed unexpectedly. Maybe you removed
        a field, changed a default, or wanted to edit some sample data?

        To fix the test, you just need to ensure the code has all the logic it
        needs to parse everything from this directory:
        - src/fides/data/sample_project/sample_connections/*.yml

        See src/fides/api/database/samples.py for details.

        Sorry for the trouble, but we want to ensure there isn't a subtle bug
        sneaking into our sample project code!
        """
        error_message = (
            "Unexpected error loading sample connections; did you make changes to the sample project? "
            "See tests/ctl/api/test_seed.py for details."
        )
        connections = []
        try:
            connections = samples.load_sample_connections_from_project()
        except Exception as exc:
            print(exc)
            assert False, error_message

        # Assert that only the connections with all their secrets are returned
        assert len(connections) == 4
        assert sorted([e.key for e in connections]) == [
            "cookie_house_custom_request_fields_database",
            "cookie_house_customer_database_mongodb",
            "cookie_house_postgresql_database",
            "stripe_connector",
        ]

        # Assert that variable expansion worked as expected
        postgres = [e for e in connections if e.connection_type == "postgres"][
            0
        ].model_dump(mode="json")
        assert postgres["secrets"]["host"] == "test-var-expansion"
        assert postgres["secrets"]["port"] == 9090

    @patch.dict(
        os.environ,
        {
            "TEST_VAR_1": "var-1",
            "TEST_VAR_2": "var-2",
        },
        clear=True,
    )
    async def test_load_sample_yaml_file(self):
        """
        Test that we can safely load, parse, and perform variable expansion on
        a sample project file.
        """
        sample_str = dedent(
            """\
            connection:
              - key: test_connection
                name: Test Connector $TEST_VAR_1
                connection_type: postgres
                access: write
                secrets:
                  host: test-host
                  port: 9001
                  dbname: $TEST_VAR_2
                  username: user-${TEST_VAR_2}
                  password: ${TEST_VAR_1}-${TEST_VAR_2}
        """
        )
        sample_file = io.StringIO(sample_str)

        sample_dict = samples.load_sample_yaml_file(sample_file)
        assert list(sample_dict.keys()) == ["connection"]
        sample_connection = sample_dict["connection"][0]
        assert sample_connection["key"] == "test_connection"
        assert sample_connection["name"] == "Test Connector var-1"
        assert sample_connection["connection_type"] == "postgres"
        assert sample_connection["access"] == "write"
        assert sample_connection["secrets"]["host"] == "test-host"
        assert sample_connection["secrets"]["port"] == 9001
        assert sample_connection["secrets"]["dbname"] == "var-2"
        assert sample_connection["secrets"]["username"] == "user-var-2"
        assert sample_connection["secrets"]["password"] == "var-1-var-2"
