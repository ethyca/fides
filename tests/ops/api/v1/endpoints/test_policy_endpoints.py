import json
from typing import List
from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from fides.api.models.client import ClientDetail
from fides.api.models.policy import ActionType, DrpAction, Policy, Rule, RuleTarget
from fides.api.service.masking.strategy.masking_strategy_nullify import (
    NullMaskingStrategy,
)
from fides.api.util.data_category import DataCategory, generate_fides_data_categories
from fides.common.api import scope_registry as scopes
from fides.common.api.v1.urn_registry import POLICY_DETAIL as POLICY_DETAIL_URI
from fides.common.api.v1.urn_registry import POLICY_LIST as POLICY_CREATE_URI
from fides.common.api.v1.urn_registry import RULE_DETAIL as RULE_DETAIL_URI
from fides.common.api.v1.urn_registry import RULE_LIST as RULE_CREATE_URI
from fides.common.api.v1.urn_registry import (
    RULE_TARGET_DETAIL,
    RULE_TARGET_LIST,
    V1_URL_PREFIX,
)


class TestGetPolicies:
    @pytest.fixture(scope="function")
    def url(self, oauth_client) -> str:
        return V1_URL_PREFIX + POLICY_CREATE_URI

    def test_get_policies_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_policies_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_get_policies_with_rules(
        self, api_client: TestClient, generate_auth_header, policy, url
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        assert data["total"] == 1

        policy_data = data["items"][0]
        assert policy_data["key"] == policy.key
        assert "rules" in policy_data
        assert len(policy_data["rules"]) == 1

        rule = policy_data["rules"][0]
        assert rule["key"] == "access_request_rule"
        assert rule["action_type"] == "access"
        assert rule["storage_destination"]["type"] == "s3"

    def test_pagination_ordering(
        self,
        db,
        oauth_client,
        api_client: TestClient,
        generate_auth_header,
        url,
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        policies = []
        POLICY_COUNT = 50
        for _ in range(POLICY_COUNT):
            key = str(uuid4()).replace("-", "")
            policies.append(
                Policy.create(
                    db=db,
                    data={
                        "name": key,
                        "key": key,
                        "client_id": oauth_client.id,
                    },
                )
            )

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        assert data["total"] == POLICY_COUNT

        for policy in data["items"]:
            # The most recent policy will be that which was last added to `policies`
            most_recent = policies.pop()
            assert policy["key"] == most_recent.key
            # Once we're finished we need to delete the policies, since `oauth_client` will be
            # subsequently deleted and will cause validation errors
            most_recent.delete(db=db)


class TestGetPolicyDetail:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + POLICY_DETAIL_URI.format(policy_key=policy.key)

    def test_get_policy_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_policy_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.STORAGE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_get_invalid_policy(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        url = V1_URL_PREFIX + POLICY_DETAIL_URI.format(policy_key="bad")

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 404

    def test_get_policy_returns_drp_action(
        self, api_client: TestClient, generate_auth_header, policy_drp_action, url
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.get(
            V1_URL_PREFIX + POLICY_DETAIL_URI.format(policy_key=policy_drp_action.key),
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(json.dumps(resp.json(), indent=2))
        assert data["key"] == policy_drp_action.key
        assert data["drp_action"] == DrpAction.access.value
        assert "rules" in data
        assert len(data["rules"]) == 1

        rule = data["rules"][0]
        assert rule["key"] == "access_request_rule_drp"
        assert rule["action_type"] == "access"
        assert rule["storage_destination"]["type"] == "s3"

    def test_get_policy_returns_rules(
        self, api_client: TestClient, generate_auth_header, policy, url
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        print(json.dumps(resp.json(), indent=2))
        assert data["key"] == policy.key
        assert "rules" in data
        assert len(data["rules"]) == 1

        rule = data["rules"][0]
        assert rule["key"] == "access_request_rule"
        assert rule["action_type"] == "access"
        assert rule["storage_destination"]["type"] == "s3"

    def test_get_policies_returns_rules(
        self,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.get(
            V1_URL_PREFIX + POLICY_CREATE_URI,
            headers=auth_header,
        )
        assert resp.status_code == 200
        print(json.dumps(resp.json(), indent=2))
        print(f"POLICY = {policy.__dict__}")
        print(f"RULES = {policy.rules}")
        print(f"RULES = {policy.rules[0]}")
        print(f"RULES = {policy.rules[0].__dict__}")
        data = resp.json()

        assert "items" in data
        assert data["total"] == 1

        policy_data = data["items"][0]
        assert policy_data["key"] == policy.key
        assert "rules" in policy_data
        assert len(policy_data["rules"]) == 1

        rule = policy_data["rules"][0]
        assert rule["key"] == "access_request_rule"
        assert rule["action_type"] == "access"
        assert rule["storage_destination"]["type"] == "s3"


class TestGetRules:
    @pytest.fixture(scope="function")
    def url(self, policy: Policy) -> str:
        return V1_URL_PREFIX + RULE_CREATE_URI.format(policy_key=policy.key)

    def test_get_rules_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_rules_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    @pytest.mark.usefixtures("policy_drp_action")
    def test_get_rules(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        policy: Policy,
        url,
    ):
        # since we have more than one policy fixture, we expect to have
        # more than one policy, and therefore more than one rule, in the db
        all_policies = Policy.query(db=db).all()
        assert len(all_policies) > 1
        all_rules = Rule.query(db=db).all()
        assert len(all_rules) > 1

        auth_header = generate_auth_header(scopes=[scopes.RULE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        # but because our GET request specifies only a single policy,
        # we expect to only get back its one rule in our response
        assert data["total"] == 1

        access_rule: Rule = policy.get_rules_for_action(ActionType.access.value)[0]

        rule_data = data["items"][0]
        assert rule_data["name"] == access_rule.name
        assert rule_data["key"] == "access_request_rule"
        assert rule_data["action_type"] == access_rule.action_type
        assert rule_data["storage_destination"]["type"] == "s3"

        assert "targets" in rule_data
        assert len(rule_data["targets"]) == 1

        rule_target_data = rule_data["targets"][0]
        rule_target_data["data_category"] = access_rule.get_target_data_categories()

    def test_pagination_ordering_rules(
        self,
        db,
        oauth_client,
        api_client: TestClient,
        generate_auth_header,
        url,
        policy,
        storage_config,
    ):
        auth_header = generate_auth_header(scopes=[scopes.RULE_READ])
        rules = []
        RULE_COUNT = 50
        for _ in range(RULE_COUNT):
            key = str(uuid4()).replace("-", "")
            rules.append(
                Rule.create(
                    db=db,
                    data={
                        "name": key,
                        "key": key,
                        "action_type": ActionType.access.value,
                        "storage_destination_id": storage_config.id,
                        "policy_id": policy.id,
                    },
                )
            )

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data

        # 1 additional rule was added to the db as part of the `policy` fixture
        assert data["total"] == RULE_COUNT + 1

        for rule in data["items"]:
            # The most recent rule will be that which was last added to `rules`
            most_recent = rules.pop()
            assert rule["key"] == most_recent.key
            # Once we're finished we need to delete the rules, since `oauth_client` will be
            # subsequently deleted and will cause validation errors
            most_recent.delete(db=db)


class TestGetRuleDetail:
    @pytest.fixture(scope="function")
    def rule(self, policy: Policy) -> Rule:
        return policy.get_rules_for_action(ActionType.access.value)[0]

    @pytest.fixture(scope="function")
    def url(self, policy: Policy, rule: Rule) -> str:
        return V1_URL_PREFIX + RULE_DETAIL_URI.format(
            policy_key=policy.key,
            rule_key=rule.key,
        )

    def test_get_rule_detail_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_rule_detail_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_get_invalid_rule(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        auth_header = generate_auth_header(scopes=[scopes.RULE_READ])
        url = V1_URL_PREFIX + RULE_DETAIL_URI.format(
            policy_key=policy.key, rule_key="bad"
        )

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 404

    def test_get_rule_returns_rule_target(
        self, api_client: TestClient, generate_auth_header, policy, rule: Rule, url
    ):
        auth_header = generate_auth_header(scopes=[scopes.RULE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"] == rule.key
        assert "targets" in data
        assert len(data["targets"]) == 1

        rule_target_data = data["targets"][0]
        rule_target_data["data_category"] = rule.get_target_data_categories()


class TestGetRuleTargets:
    @pytest.fixture(scope="function")
    def rule(self, policy: Policy) -> Rule:
        return policy.get_rules_for_action(ActionType.access.value)[0]

    @pytest.fixture(scope="function")
    def rule_target(self, db, policy: Policy, rule: Rule) -> RuleTarget:
        rule_targets: List[RuleTarget] = RuleTarget.filter(
            db=db, conditions=(RuleTarget.rule_id == rule.id)
        ).all()
        assert len(rule_targets) == 1
        return rule_targets[0]

    @pytest.fixture(scope="function")
    def url(self, policy: Policy, rule: Rule) -> str:
        return V1_URL_PREFIX + RULE_TARGET_LIST.format(
            policy_key=policy.key, rule_key=rule.key
        )

    def test_get_rule_targets_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_rule_targets_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    @pytest.mark.usefixtures("policy_drp_action")
    def test_get_rule_targets(
        self,
        db,
        api_client: TestClient,
        generate_auth_header,
        rule_target: RuleTarget,
        url,
    ):
        # since we have more than one policy fixture, we expect to have
        # more than one policy, and therefore more than one rule target, in the db
        all_policies = Policy.query(db=db).all()
        assert len(all_policies) > 1
        all_rules = Rule.query(db=db).all()
        assert len(all_rules) > 1
        all_rule_targets = RuleTarget.query(db=db).all()
        assert len(all_rule_targets) > 1

        auth_header = generate_auth_header(scopes=[scopes.RULE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert "items" in data
        # but because our GET request specifies only a single policy + rule,
        # we expect to only get back its one rule target in our response
        assert data["total"] == 1

        rule_target_data = data["items"][0]
        assert rule_target_data["name"] == rule_target.name
        assert rule_target_data["key"] == rule_target.key
        assert rule_target_data["data_category"] == rule_target.data_category


class TestGetRuleTargetDetail:
    @pytest.fixture(scope="function")
    def rule(self, policy: Policy) -> Rule:
        return policy.get_rules_for_action(ActionType.access.value)[0]

    @pytest.fixture(scope="function")
    def rule_target(self, db, policy: Policy, rule: Rule) -> RuleTarget:
        rule_targets: List[RuleTarget] = RuleTarget.filter(
            db=db, conditions=(RuleTarget.rule_id == rule.id)
        ).all()
        assert len(rule_targets) == 1
        return rule_targets[0]

    @pytest.fixture(scope="function")
    def url(self, policy: Policy, rule: Rule, rule_target: RuleTarget) -> str:
        return V1_URL_PREFIX + RULE_TARGET_DETAIL.format(
            policy_key=policy.key,
            rule_key=rule.key,
            rule_target_key=rule_target.key,
        )

    def test_get_rule_target_detail_unauthenticated(self, url, api_client):
        resp = api_client.get(url)
        assert resp.status_code == 401

    def test_get_rule_target_detail_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 403

    def test_get_invalid_rule_target(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy,
        rule,
    ):
        auth_header = generate_auth_header(scopes=[scopes.RULE_READ])
        url = V1_URL_PREFIX + RULE_TARGET_DETAIL.format(
            policy_key=policy.key, rule_key=rule.key, rule_target_key="bad"
        )

        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 404

    def test_get_rule_target(
        self,
        api_client: TestClient,
        generate_auth_header,
        policy,
        rule: Rule,
        rule_target: RuleTarget,
        url,
    ):
        auth_header = generate_auth_header(scopes=[scopes.RULE_READ])
        resp = api_client.get(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"] == rule_target.key
        assert data["name"] == rule_target.name
        assert "data_category" in data
        assert data["data_category"] == rule_target.data_category


class TestCreatePolicies:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + POLICY_CREATE_URI

    @pytest.fixture(scope="function")
    def payload(self, storage_config):
        return [
            {
                "name": "policy 1",
                "action_type": "erasure",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
            },
            {
                "name": "policy 2",
                "action_type": "access",
                "data_category": DataCategory("user").value,
                "execution_timeframe": 5,
                "storage_destination_key": storage_config.key,
            },
        ]

    def test_create_policies_unauthenticated(
        self, url, api_client: TestClient, payload
    ):
        resp = api_client.patch(url, json=payload)
        assert resp.status_code == 401

    def test_create_policies_wrong_scope(
        self, url, api_client: TestClient, payload, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.patch(url, headers=auth_header, json=payload)
        assert resp.status_code == 403

    def test_create_polices_limit_exceeded(
        self, api_client: TestClient, generate_auth_header, url, storage_config
    ):
        payload = []
        for i in range(0, 51):
            payload.append(
                {
                    "name": f"policy {i}",
                    "action_type": "erasure",
                    "data_category": DataCategory("user").value,
                    "storage_destination_key": storage_config.key,
                }
            )

        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)
        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "List should have at most 50 items after validation, not 51"
        )

    def test_create_multiple_policies(
        self,
        api_client: TestClient,
        db,
        generate_auth_header,
        storage_config,
        url,
        payload,
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=payload, headers=auth_header)
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["succeeded"]) == 2

        assert data["succeeded"][0]["execution_timeframe"] is None
        assert data["succeeded"][1]["execution_timeframe"] == 5

        elements = data["succeeded"]
        for el in elements:
            pol = Policy.filter(db=db, conditions=(Policy.key == el["key"])).first()
            pol.delete(db=db)

    def test_create_policy_with_duplicate_key(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy,
        storage_config,
    ):
        data = [
            {
                "name": policy.name,
                "action_type": "erasure",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
            },
            {
                "name": policy.name,
                "action_type": "erasure",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
            },
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["failed"]) == 2

    def test_create_policy_with_duplicate_drp_action(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy_drp_action,
        storage_config,
    ):
        data = [
            {
                "name": "policy with pre-existing drp action",
                "action_type": ActionType.access.value,
                "drp_action": DrpAction.access.value,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["failed"]) == 1

    def test_update_policy_with_duplicate_drp_action(
        self,
        db,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy_drp_action,
        storage_config,
    ):
        # creates a new drp policy
        data = [
            {
                "key": "erasure_drp_policy",
                "name": "erasure drp policy",
                "action_type": ActionType.erasure.value,
                "drp_action": DrpAction.deletion.value,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        valid_drp_resp = api_client.patch(url, json=data, headers=auth_header)
        valid_response_data = valid_drp_resp.json()["succeeded"]
        assert valid_drp_resp.status_code == 200

        # try to update the above policy with a pre-existing drp action
        data = [
            {
                "key": "erasure_drp_policy",
                "name": "policy with pre-existing drp action",
                "action_type": ActionType.access.value,
                "drp_action": DrpAction.access.value,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["failed"]) == 1

        pol = Policy.filter(
            db=db, conditions=(Policy.key == valid_response_data[0]["key"])
        ).first()
        pol.delete(db=db)

    def test_update_policy_with_drp_action(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy,
        storage_config,
    ):
        data = [
            {
                "key": policy.key,
                "name": "updated name",
                "action_type": ActionType.access.value,
                "drp_action": DrpAction.access.value,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

    def test_create_policy_invalid_drp_action(
        self, url, api_client: TestClient, payload, generate_auth_header, storage_config
    ):
        payload = [
            {
                "name": "policy 1",
                "action_type": "erasure",
                "drp_action": "invalid",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=payload, headers=auth_header)
        assert resp.status_code == 422

        response_body = json.loads(resp.text)
        assert (
            "Input should be 'access', 'deletion', 'sale:opt_out', 'sale:opt_in', 'access:categories' or 'access:specific'"
            == response_body["detail"][0]["msg"]
        )

    def test_create_policy_with_drp_action(
        self,
        db,
        url,
        api_client: TestClient,
        payload,
        generate_auth_header,
        storage_config,
    ):
        payload = [
            {
                "name": "policy 1",
                "action_type": "erasure",
                "drp_action": "deletion",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=payload, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

        pol = Policy.filter(
            db=db, conditions=(Policy.key == response_data[0]["key"])
        ).first()
        pol.delete(db=db)

    def test_create_policy_creates_key(
        self, db, api_client: TestClient, generate_auth_header, storage_config, url
    ):
        data = [
            {
                "name": "test create policy api",
                "action_type": "erasure",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

        pol = Policy.filter(
            db=db, conditions=(Policy.key == response_data[0]["key"])
        ).first()
        pol.delete(db=db)

    def test_create_policy_as_root(
        self, db, api_client: TestClient, root_auth_header, storage_config, url
    ):
        data = [
            {
                "name": "test create policy api",
                "action_type": "erasure",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
            }
        ]
        auth_header = root_auth_header
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

        pol = Policy.filter(
            db=db, conditions=(Policy.key == response_data[0]["key"])
        ).first()
        pol.delete(db=db)

    def test_create_policy_with_key(
        self,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        storage_config,
    ):
        key = "here_is_a_key"
        data = [
            {
                "name": "test create policy api",
                "action_type": "erasure",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
                "key": key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

        policy_data = response_data[0]
        assert policy_data["key"] == key

        pol = Policy.filter(
            db=db, conditions=(Policy.key == policy_data["key"])
        ).first()
        pol.delete(db=db)

    def test_create_policy_with_invalid_key(
        self,
        url,
        db,
        api_client: TestClient,
        generate_auth_header,
        storage_config,
    ):
        key = "here*is*an*invalid*key"
        data = [
            {
                "name": "test create policy api",
                "action_type": "erasure",
                "data_category": DataCategory("user").value,
                "storage_destination_key": storage_config.key,
                "key": key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 422
        assert (
            json.loads(resp.text)["detail"][0]["msg"]
            == "Value error, FidesKeys must only contain alphanumeric characters, '.', '_', '<', '>' or '-'. Value provided: here*is*an*invalid*key"
        )

    def test_create_policy_already_exists(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        data = [
            {
                "name": "test create policy api",
                "key": policy.key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.POLICY_CREATE_OR_UPDATE])
        resp = api_client.patch(url, json=data, headers=auth_header)
        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1


class TestCreateRules:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        return V1_URL_PREFIX + RULE_CREATE_URI.format(policy_key=policy.key)

    def test_create_rules_unauthenticated(self, url, api_client):
        resp = api_client.patch(url, json={})
        assert resp.status_code == 401

    def test_create_rules_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.patch(url, headers=auth_header, json={})
        assert resp.status_code == 403

    def test_create_rules_invalid_policy(
        self, url, api_client: TestClient, generate_auth_header, policy, storage_config
    ):
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        url = V1_URL_PREFIX + RULE_CREATE_URI.format(policy_key="bad_key")

        data = [
            {
                "name": "test access rule",
                "action_type": ActionType.access.value,
                "storage_destination_key": storage_config.key,
            }
        ]

        resp = api_client.patch(url, headers=auth_header, json=data)
        assert resp.status_code == 404

    def test_create_rules_mismatching_drp_policy(
        self,
        api_client: TestClient,
        generate_auth_header,
        policy_drp_action,
        storage_config,
    ):
        data = [
            {
                "name": "test access rule",
                "action_type": ActionType.erasure.value,
                "storage_destination_key": storage_config.key,
            }
        ]
        url = V1_URL_PREFIX + RULE_CREATE_URI.format(policy_key=policy_drp_action.key)
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            url,
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["failed"]
        assert len(response_data) == 1

    def test_create_rules_invalid_storage_destination(
        self,
        api_client: TestClient,
        generate_auth_header,
        policy,
        storage_config,
    ):
        data = [
            {
                "name": "test access rule",
                "action_type": ActionType.access.value,
                "storage_destination_key": "invalid_storage_key",
            }
        ]
        url = V1_URL_PREFIX + RULE_CREATE_URI.format(policy_key=policy.key)
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            url,
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["failed"]
        assert len(response_data) == 1

    def test_create_rules_limit_exceeded(
        self, api_client: TestClient, generate_auth_header, url, storage_config
    ):
        payload = []
        for i in range(0, 51):
            payload.append(
                {
                    "name": f"test access rule {i}",
                    "action_type": ActionType.access.value,
                    "storage_destination_key": storage_config.key,
                }
            )

        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        response = api_client.patch(url, headers=auth_header, json=payload)

        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "List should have at most 50 items after validation, not 51"
        )

    def test_create_access_rule_for_policy(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        policy,
        storage_config,
    ):
        data = [
            {
                "name": "test access rule",
                "action_type": ActionType.access.value,
                "storage_destination_key": storage_config.key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            url,
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        rule_data = response_data[0]
        assert "storage_destination" in rule_data
        assert "key" in rule_data["storage_destination"]
        assert "secrets" not in rule_data["storage_destination"]

    def test_create_access_rule_for_policy_as_root(
        self,
        api_client: TestClient,
        url,
        root_auth_header,
        policy,
        storage_config,
    ):
        data = [
            {
                "name": "test access rule",
                "action_type": ActionType.access.value,
                "storage_destination_key": storage_config.key,
            }
        ]
        auth_header = root_auth_header
        resp = api_client.patch(
            url,
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        rule_data = response_data[0]
        assert "storage_destination" in rule_data
        assert "key" in rule_data["storage_destination"]
        assert "secrets" not in rule_data["storage_destination"]

    def test_create_access_rule_for_policy_no_storage_specified(
        self,
        api_client: TestClient,
        url,
        generate_auth_header,
        policy,
        storage_config,
    ):
        data = [
            {
                "name": "test access rule",
                "action_type": ActionType.access.value,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            url,
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        rule_data = response_data[0]
        assert (
            "storage_destination" not in rule_data
            or rule_data["storage_destination"] is None
        )
        assert rule_data["name"] == "test access rule"

    def test_create_erasure_rule_for_policy(
        self,
        url,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        data = [
            {
                "name": "test erasure rule",
                "action_type": ActionType.erasure.value,
                "masking_strategy": {
                    "strategy": NullMaskingStrategy.name,
                    "configuration": {},
                },
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            url,
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1
        rule_data = response_data[0]
        assert "masking_strategy" in rule_data
        masking_strategy_data = rule_data["masking_strategy"]
        assert masking_strategy_data["strategy"] == NullMaskingStrategy.name
        assert "configuration" not in masking_strategy_data

    def test_update_rule_policy_id_fails(
        self,
        api_client: TestClient,
        oauth_client: ClientDetail,
        storage_config,
        db,
        generate_auth_header,
        policy,
    ):
        rule = policy.rules[0]

        another_policy = Policy.create(
            db=db,
            data={
                "name": "Second Access Request policy",
                "key": "second_access_request_policy",
                "client_id": oauth_client.id,
            },
        )

        url = V1_URL_PREFIX + RULE_CREATE_URI.format(policy_key=another_policy.key)

        data = [
            {
                "name": rule.name,
                "key": rule.key,
                "action_type": ActionType.access.value,
                "storage_destination_key": storage_config.key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            url,
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["failed"]
        assert len(response_data) == 1
        assert (
            response_data[0]["message"]
            == f"Rule with identifier {rule.key} belongs to another policy."
        )

        updated_rule = Rule.get(db=db, object_id=rule.id)
        db.expire(updated_rule)
        assert updated_rule.policy_id == policy.id

        another_policy.delete(db=db)


class TestDeleteRule:
    @pytest.fixture(scope="function")
    def url(self, oauth_client: ClientDetail, policy) -> str:
        rule = policy.rules[0]

        return V1_URL_PREFIX + RULE_DETAIL_URI.format(
            policy_key=policy.key,
            rule_key=rule.key,
        )

    def test_delete_rule_unauthenticated(self, url, api_client):
        resp = api_client.delete(url)
        assert resp.status_code == 401

    def test_delete_rule_wrong_scope(
        self, url, api_client: TestClient, generate_auth_header
    ):
        auth_header = generate_auth_header(scopes=[scopes.POLICY_READ])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == 403

    def test_delete_rule_invalid_policy(
        self, api_client: TestClient, generate_auth_header, policy
    ):
        rule = policy.rules[0]

        url = V1_URL_PREFIX + RULE_DETAIL_URI.format(
            policy_key="bad_policy",
            rule_key=rule.key,
        )

        auth_header = generate_auth_header(scopes=[scopes.RULE_DELETE])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == 404

    def test_delete_rule_invalid_rule(
        self, api_client: TestClient, generate_auth_header, policy
    ):
        url = V1_URL_PREFIX + RULE_DETAIL_URI.format(
            policy_key=policy.key,
            rule_key="bad_rule",
        )

        auth_header = generate_auth_header(scopes=[scopes.RULE_DELETE])
        resp = api_client.delete(url, headers=auth_header)
        assert resp.status_code == 404

    def test_delete_rule_for_policy(
        self, api_client: TestClient, generate_auth_header, policy, url
    ):
        auth_header = generate_auth_header(scopes=[scopes.RULE_DELETE])
        resp = api_client.delete(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 204


class TestRuleTargets:
    def get_rule_url(self, policy_key, rule_key):
        return V1_URL_PREFIX + RULE_TARGET_LIST.format(
            policy_key=policy_key,
            rule_key=rule_key,
        )

    def get_rule_target_url(self, policy_key, rule_key, rule_target_key):
        return V1_URL_PREFIX + RULE_TARGET_DETAIL.format(
            policy_key=policy_key,
            rule_key=rule_key,
            rule_target_key=rule_target_key,
        )

    def test_create_rule_targets(
        self,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        rule = policy.rules[0]
        data = [
            {
                "data_category": DataCategory("user.name").value,
            },
            {
                "data_category": DataCategory("user.contact.email").value,
            },
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            self.get_rule_url(policy.key, rule.key),
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 2

    def test_create_rule_targets_as_root(
        self,
        api_client: TestClient,
        root_auth_header,
        policy,
    ):
        rule = policy.rules[0]
        data = [
            {
                "data_category": DataCategory("user.name").value,
            },
            {
                "data_category": DataCategory("user.contact.email").value,
            },
        ]
        auth_header = root_auth_header
        resp = api_client.patch(
            self.get_rule_url(policy.key, rule.key),
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 2

    def test_create_rule_target_with_custom_category(
        self,
        api_client: TestClient,
        generate_auth_header,
        policy,
        custom_data_category,
    ):
        rule = policy.rules[0]
        data = [
            {
                "data_category": custom_data_category.fides_key,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            self.get_rule_url(policy.key, rule.key),
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

    def test_create_rule_target_with_invalid_category(
        self,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        rule = policy.rules[0]
        invalid_data_category = "invalid_category"
        data = [
            {
                "data_category": invalid_data_category,
            }
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            self.get_rule_url(policy.key, rule.key),
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 422
        assert (
            resp.json()["detail"]
            == f"Invalid data categories: ['{invalid_data_category}']"
        )

    def test_create_duplicate_rule_targets(
        self,
        api_client: TestClient,
        generate_auth_header,
        policy,
    ):
        rule = policy.rules[0]
        data_category = DataCategory("user.name").value
        data = [
            {
                "data_category": data_category,
                "name": "this-is-a-test",
                "key": "this_is_a_test",
            },
            {
                "data_category": data_category,
                "name": "this-is-another-test",
                "key": "this_is_another_test",
            },
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            self.get_rule_url(policy.key, rule.key),
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        assert len(resp.json()["succeeded"]) == 1
        assert len(resp.json()["failed"]) == 1
        assert (
            resp.json()["failed"][0]["message"]
            == f"DataCategory {data_category} is already specified on Rule with ID {rule.id}"
        )

    def test_create_targets_limit_exceeded(
        self,
        api_client: TestClient,
        generate_auth_header,
        storage_config,
        policy,
    ):
        categories = [e.value for e in generate_fides_data_categories()]

        rule = policy.rules[0]
        existing_target = rule.targets[0]

        payload = []
        for i in range(0, 51):
            payload.append(
                {
                    "data_category": categories[i],
                    "key": existing_target.key,
                },
            )

        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        response = api_client.patch(
            self.get_rule_url(policy.key, rule.key), headers=auth_header, json=payload
        )

        assert 422 == response.status_code
        assert (
            json.loads(response.text)["detail"][0]["msg"]
            == "List should have at most 50 items after validation, not 51"
        )

    def test_update_rule_targets(
        self,
        api_client: TestClient,
        db,
        generate_auth_header,
        policy,
    ):
        rule = policy.rules[0]
        existing_target = rule.targets[0]
        updated_data_category = DataCategory("user.name").value
        data = [
            {
                "data_category": updated_data_category,
                "key": existing_target.key,
            },
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            self.get_rule_url(policy.key, rule.key),
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["succeeded"]
        assert len(response_data) == 1

        updated_target = RuleTarget.get(db=db, object_id=existing_target.id)
        db.expire(updated_target)

        assert updated_target.data_category == updated_data_category
        assert updated_target.rule_id == existing_target.rule_id
        assert updated_target.key == existing_target.key
        assert updated_target.name == existing_target.name

    def test_update_rule_target_rule_id_fails(
        self,
        api_client: TestClient,
        oauth_client: ClientDetail,
        storage_config,
        db,
        generate_auth_header,
        policy,
    ):
        rule = policy.rules[0]
        another_rule = Rule.create(
            db=db,
            data={
                "action_type": ActionType.access.value,
                "client_id": oauth_client.id,
                "name": "Example Access Rule",
                "policy_id": policy.id,
                "storage_destination_id": storage_config.id,
            },
        )
        existing_target = rule.targets[0]
        updated_data_category = DataCategory("user.name").value
        data = [
            {
                "data_category": updated_data_category,
                "key": existing_target.key,
            },
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            # Here we send the request to the URL corresponding to a different rule entirely
            self.get_rule_url(policy.key, another_rule.key),
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        response_data = resp.json()["failed"]
        assert len(response_data) == 1
        assert (
            response_data[0]["message"]
            == f"RuleTarget with identifier {existing_target.key} belongs to another rule."
        )

        updated_target = RuleTarget.get(db=db, object_id=existing_target.id)
        db.expire(updated_target)
        assert updated_target.rule_id == existing_target.rule_id

        another_rule.delete(db=db)

    def test_delete_rule_target(
        self,
        api_client: TestClient,
        db,
        generate_auth_header,
        policy,
    ):
        rule = policy.rules[0]
        rule_target = rule.targets[0]
        auth_header = generate_auth_header(scopes=[scopes.RULE_DELETE])
        url = self.get_rule_target_url(
            policy_key=policy.key,
            rule_key=rule.key,
            rule_target_key=rule_target.key,
        )
        resp = api_client.delete(
            url,
            headers=auth_header,
        )
        assert resp.status_code == 204

    def test_create_conflicting_rule_targets(
        self,
        api_client: TestClient,
        db,
        generate_auth_header,
        policy,
    ):
        erasure_rule = Rule.create(
            db=db,
            data={
                "action_type": ActionType.erasure.value,
                "client_id": policy.client.id,
                "name": "Erasure Rule",
                "policy_id": policy.id,
                "masking_strategy": {
                    "strategy": NullMaskingStrategy.name,
                    "configuration": {},
                },
            },
        )

        target_1 = "user.contact.email"
        target_2 = "user.contact"
        data = [
            {
                "data_category": DataCategory(target_1).value,
            },
            {
                "data_category": DataCategory(target_2).value,
            },
        ]
        auth_header = generate_auth_header(scopes=[scopes.RULE_CREATE_OR_UPDATE])
        resp = api_client.patch(
            self.get_rule_url(policy.key, erasure_rule.key),
            json=data,
            headers=auth_header,
        )

        assert resp.status_code == 200
        succeeded = resp.json()["succeeded"]
        assert len(succeeded) == 1

        failed = resp.json()["failed"]
        assert len(failed) == 1
        assert (
            failed[0]["message"]
            == f"Policy rules are invalid, action conflict in erasure rules detected for categories {target_1} and {target_2}"
        )
