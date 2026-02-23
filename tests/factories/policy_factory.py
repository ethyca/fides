import factory

from fides.api.models.policy import ActionType, Policy, Rule, RuleTarget
from tests.factories.base import BaseFactory


class PolicyFactory(BaseFactory):
    class Meta:
        model = Policy

    name = factory.Sequence(lambda n: f"test-policy-{n}")
    key = factory.Sequence(lambda n: f"test_policy_{n}")


class RuleFactory(BaseFactory):
    class Meta:
        model = Rule

    name = factory.Sequence(lambda n: f"test-rule-{n}")
    key = factory.Sequence(lambda n: f"test_rule_{n}")
    action_type = ActionType.access.value
    policy_id = factory.LazyAttribute(lambda o: o.policy.id if o.policy else None)

    class Params:
        policy = None


class AccessRuleFactory(RuleFactory):
    action_type = ActionType.access.value


class ErasureRuleFactory(RuleFactory):
    action_type = ActionType.erasure.value


class ConsentRuleFactory(RuleFactory):
    action_type = ActionType.consent.value


class RuleTargetFactory(BaseFactory):
    class Meta:
        model = RuleTarget

    name = factory.Sequence(lambda n: f"test-rule-target-{n}")
    key = factory.Sequence(lambda n: f"test_rule_target_{n}")
    data_category = "user"
    rule_id = factory.LazyAttribute(lambda o: o.rule.id if o.rule else None)

    class Params:
        rule = None
