from typing import Generator

import pytest
from fideslang import DEFAULT_TAXONOMY, DataCategory, Organization
from sqlalchemy.ext.asyncio import AsyncSession

from fides.api.ctl.database import seed
from fides.api.ops.models.policy import ActionType, DrpAction, Policy, Rule, RuleTarget
from fides.core import api as _api
from fides.core.config import FidesConfig, get_config
from fides.lib.models.fides_user import FidesUser


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
        headers=test_config.user.auth_header,
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
        async_session: AsyncSession,
    ) -> None:
        """Should be able to add to the existing default taxonomy"""
        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=test_config.user.auth_header,
        )
        assert result.status_code == 404

        updated_default_taxonomy = DEFAULT_TAXONOMY.copy()
        updated_default_taxonomy.data_category.append(data_category)

        monkeypatch.setattr(seed, "DEFAULT_TAXONOMY", updated_default_taxonomy)
        await seed.load_default_resources(async_session)

        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=test_config.user.auth_header,
        )
        assert result.status_code == 200

    async def test_does_not_override_user_changes(
        self, test_config: FidesConfig, async_session: AsyncSession
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
            headers=test_config.user.auth_header,
        )
        assert result.status_code == 200

        await seed.load_default_resources(async_session)
        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            default_category.fides_key,
            headers=test_config.user.auth_header,
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
            headers=test_config.user.auth_header,
        )

        await seed.load_default_resources(async_session)

        result = _api.get(
            test_config.cli.server_url,
            "data_category",
            data_category.fides_key,
            headers=test_config.user.auth_header,
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


async def test_load_orginizations(loguru_caplog, async_session, monkeypatch):
    updated_default_taxonomy = DEFAULT_TAXONOMY.copy()
    current_orgs = len(updated_default_taxonomy.organization)
    updated_default_taxonomy.organization.append(
        Organization(fides_key="new_organization")
    )

    monkeypatch.setattr(seed, "DEFAULT_TAXONOMY", updated_default_taxonomy)
    await seed.load_default_organization(async_session)

    assert "INSERTED 1" in loguru_caplog.text
    assert f"SKIPPED {current_orgs}" in loguru_caplog.text
