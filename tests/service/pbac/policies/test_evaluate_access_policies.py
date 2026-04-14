"""Tests for the Access Policy v2 evaluation engine (Python implementation).

These mirror the Go tests in policy-engine/pkg/pbac/policy_evaluate_test.go
to ensure both implementations produce identical results.
"""

import pytest

from fides.service.pbac.policies.evaluate import (
    InProcessAccessPolicyEvaluator,
    ParsedPolicy,
    evaluate_policies,
    parsed_policy_from_dict,
    request_from_dict,
    result_to_dict,
)
from fides.service.pbac.policies.interface import (
    AccessEvaluationRequest,
    PolicyAction,
    PolicyDecision,
)


def req(**kwargs) -> AccessEvaluationRequest:
    """Shorthand for building AccessEvaluationRequest with defaults."""
    defaults = {
        "consumer_id": "",
        "consumer_name": "",
        "consumer_purposes": frozenset(),
        "dataset_key": "",
        "dataset_purposes": frozenset(),
    }
    defaults.update(kwargs)
    return AccessEvaluationRequest(**defaults)


class TestPriorityOrdering:
    def test_highest_priority_wins(self):
        policies = [
            ParsedPolicy(key="low-allow", priority=10, decision=PolicyDecision.ALLOW),
            ParsedPolicy(
                key="high-deny",
                priority=200,
                decision=PolicyDecision.DENY,
                action=PolicyAction(message="Highest priority wins"),
            ),
        ]
        result = evaluate_policies(policies, req(data_uses=("marketing",)))

        assert result.decision == PolicyDecision.DENY
        assert result.decisive_policy_key == "high-deny"

    def test_allow_when_matched(self):
        policies = [
            ParsedPolicy(
                key="deny-financial",
                priority=200,
                decision=PolicyDecision.DENY,
                match={"data_category": {"any": ["user.financial"]}},
            ),
            ParsedPolicy(
                key="allow-marketing",
                priority=100,
                decision=PolicyDecision.ALLOW,
                match={"data_use": {"any": ["marketing"]}},
            ),
        ]
        result = evaluate_policies(
            policies,
            req(
                data_uses=("marketing.advertising",),
                data_categories=("user.contact.email",),
            ),
        )

        assert result.decision == PolicyDecision.ALLOW
        assert result.decisive_policy_key == "allow-marketing"

    def test_catch_all_deny(self):
        policies = [
            ParsedPolicy(
                key="catch-all",
                priority=0,
                decision=PolicyDecision.DENY,
                action=PolicyAction(message="Default deny"),
            ),
        ]

        result = evaluate_policies(policies, req(data_uses=("essential",)))

        assert result.decision == PolicyDecision.DENY
        assert result.decisive_policy_key == "catch-all"
        assert result.action is not None
        assert result.action.message == "Default deny"


class TestNoDecision:
    def test_empty_policies(self):
        result = evaluate_policies([], req())
        assert result.decision == PolicyDecision.NO_DECISION

    def test_disabled_policies_skipped(self):
        policies = [
            ParsedPolicy(
                key="disabled",
                priority=100,
                enabled=False,
                decision=PolicyDecision.DENY,
            )
        ]
        result = evaluate_policies(policies, req())
        assert result.decision == PolicyDecision.NO_DECISION

    def test_no_match(self):
        policies = [
            ParsedPolicy(
                key="deny-financial",
                priority=100,
                decision=PolicyDecision.DENY,
                match={"data_category": {"any": ["user.financial"]}},
            ),
        ]
        result = evaluate_policies(
            policies, req(data_categories=("system.operations",))
        )
        assert result.decision == PolicyDecision.NO_DECISION


class TestTaxonomyMatching:
    def test_parent_matches_child(self):
        policies = [
            ParsedPolicy(
                key="deny-user",
                priority=100,
                decision=PolicyDecision.DENY,
                match={"data_category": {"any": ["user"]}},
            ),
        ]
        result = evaluate_policies(
            policies, req(data_categories=("user.contact.email",))
        )
        assert result.decision == PolicyDecision.DENY

    def test_child_does_not_match_parent(self):
        policies = [
            ParsedPolicy(
                key="deny-child",
                priority=100,
                decision=PolicyDecision.DENY,
                match={"data_category": {"any": ["user.contact.email"]}},
            ),
        ]
        result = evaluate_policies(policies, req(data_categories=("user.contact",)))
        assert result.decision == PolicyDecision.NO_DECISION

    def test_no_dot_boundary_false_positive(self):
        policies = [
            ParsedPolicy(
                key="deny-user",
                priority=100,
                decision=PolicyDecision.DENY,
                match={"data_category": {"any": ["user"]}},
            ),
        ]
        result = evaluate_policies(policies, req(data_categories=("user_data",)))
        assert result.decision == PolicyDecision.NO_DECISION

    def test_match_all_requires_every_value(self):
        policies = [
            ParsedPolicy(
                key="require-both",
                priority=100,
                decision=PolicyDecision.DENY,
                match={"data_category": {"all": ["user.contact", "user.financial"]}},
            ),
        ]

        result1 = evaluate_policies(
            policies, req(data_categories=("user.contact.email",))
        )
        assert result1.decision == PolicyDecision.NO_DECISION

        result2 = evaluate_policies(
            policies,
            req(data_categories=("user.contact.email", "user.financial.bank_account")),
        )
        assert result2.decision == PolicyDecision.DENY


class TestUnlessConsent:
    def test_opt_out_inverts_allow(self):
        policies = [
            ParsedPolicy(
                key="allow-unless-optout",
                priority=100,
                decision=PolicyDecision.ALLOW,
                match={"data_use": {"any": ["marketing"]}},
                unless=[
                    {
                        "type": "consent",
                        "privacy_notice_key": "do_not_sell",
                        "requirement": "opt_out",
                    }
                ],
                action=PolicyAction(message="User opted out"),
            ),
        ]
        result = evaluate_policies(
            policies,
            req(
                data_uses=("marketing.advertising",),
                context={"consent": {"do_not_sell": "opt_out"}},
            ),
        )

        assert result.decision == PolicyDecision.DENY
        assert result.unless_triggered is True

    def test_consent_not_triggered_allow_stands(self):
        policies = [
            ParsedPolicy(
                key="allow-unless-optout",
                priority=100,
                decision=PolicyDecision.ALLOW,
                match={"data_use": {"any": ["marketing"]}},
                unless=[
                    {
                        "type": "consent",
                        "privacy_notice_key": "do_not_sell",
                        "requirement": "opt_out",
                    }
                ],
            ),
        ]
        result = evaluate_policies(
            policies,
            req(
                data_uses=("marketing.advertising",),
                context={"consent": {"do_not_sell": "opt_in"}},
            ),
        )
        assert result.decision == PolicyDecision.ALLOW
        assert result.unless_triggered is False


class TestUnlessGeo:
    def test_deny_suppressed_continues_to_next(self):
        policies = [
            ParsedPolicy(
                key="deny-unless-geo",
                priority=200,
                decision=PolicyDecision.DENY,
                unless=[
                    {
                        "type": "geo_location",
                        "field": "environment.geo_location",
                        "operator": "in",
                        "values": ["US-CA"],
                    }
                ],
            ),
            ParsedPolicy(
                key="fallback-allow", priority=100, decision=PolicyDecision.ALLOW
            ),
        ]
        result = evaluate_policies(
            policies, req(context={"environment": {"geo_location": "US-CA"}})
        )

        assert result.decision == PolicyDecision.ALLOW
        assert result.decisive_policy_key == "fallback-allow"
        assert len(result.evaluated_policies) == 2
        assert result.evaluated_policies[0].result == "SUPPRESSED"
        assert result.evaluated_policies[1].result == "ALLOW"


class TestUnlessDataFlow:
    def test_egress_triggers_unless(self):
        policies = [
            ParsedPolicy(
                key="allow-unless-egress",
                priority=100,
                decision=PolicyDecision.ALLOW,
                unless=[
                    {
                        "type": "data_flow",
                        "direction": "egress",
                        "operator": "any_of",
                        "systems": ["external_vendor"],
                    }
                ],
            ),
        ]
        result = evaluate_policies(
            policies,
            req(context={"data_flows": {"egress": ["external_vendor", "partner_api"]}}),
        )
        assert result.decision == PolicyDecision.DENY


class TestUnlessMultipleConstraints:
    def test_all_must_trigger(self):
        policies = [
            ParsedPolicy(
                key="allow-unless-both",
                priority=100,
                decision=PolicyDecision.ALLOW,
                unless=[
                    {
                        "type": "consent",
                        "privacy_notice_key": "do_not_sell",
                        "requirement": "opt_out",
                    },
                    {
                        "type": "geo_location",
                        "field": "environment.geo_location",
                        "operator": "in",
                        "values": ["US-CA"],
                    },
                ],
            ),
        ]

        result1 = evaluate_policies(
            policies,
            req(
                context={
                    "consent": {"do_not_sell": "opt_out"},
                    "environment": {"geo_location": "US-NY"},
                }
            ),
        )
        assert result1.decision == PolicyDecision.ALLOW

        result2 = evaluate_policies(
            policies,
            req(
                context={
                    "consent": {"do_not_sell": "opt_out"},
                    "environment": {"geo_location": "US-CA"},
                }
            ),
        )
        assert result2.decision == PolicyDecision.DENY


class TestMatchDataSubject:
    def test_data_subject_matches(self):
        policies = [
            ParsedPolicy(
                key="deny-employee",
                priority=100,
                decision=PolicyDecision.DENY,
                match={"data_subject": {"any": ["employee"]}},
            ),
        ]
        result = evaluate_policies(policies, req(data_subjects=("employee",)))
        assert result.decision == PolicyDecision.DENY

    def test_data_subject_no_match(self):
        policies = [
            ParsedPolicy(
                key="deny-employee",
                priority=100,
                decision=PolicyDecision.DENY,
                match={"data_subject": {"any": ["employee"]}},
            ),
        ]
        result = evaluate_policies(policies, req(data_subjects=("customer",)))
        assert result.decision == PolicyDecision.NO_DECISION

    def test_three_dimensions_all_must_match(self):
        policies = [
            ParsedPolicy(
                key="specific",
                priority=100,
                decision=PolicyDecision.DENY,
                match={
                    "data_use": {"any": ["marketing"]},
                    "data_category": {"any": ["user.contact"]},
                    "data_subject": {"any": ["customer"]},
                },
            ),
        ]
        result = evaluate_policies(
            policies,
            req(
                data_uses=("marketing.advertising",),
                data_categories=("user.contact.email",),
                data_subjects=("customer",),
            ),
        )
        assert result.decision == PolicyDecision.DENY

        result2 = evaluate_policies(
            policies,
            req(
                data_uses=("marketing.advertising",),
                data_categories=("user.contact.email",),
                data_subjects=("employee",),
            ),
        )
        assert result2.decision == PolicyDecision.NO_DECISION


class TestMatchCombined:
    def test_any_and_all_on_different_dimensions(self):
        policies = [
            ParsedPolicy(
                key="combined",
                priority=100,
                decision=PolicyDecision.DENY,
                match={
                    "data_use": {"any": ["marketing"]},
                    "data_category": {"all": ["user.contact", "user.financial"]},
                },
            ),
        ]
        result = evaluate_policies(
            policies,
            req(
                data_uses=("marketing.advertising",),
                data_categories=("user.contact.email", "user.financial.bank_account"),
            ),
        )
        assert result.decision == PolicyDecision.DENY

        result2 = evaluate_policies(
            policies,
            req(
                data_uses=("marketing.advertising",),
                data_categories=("user.contact.email",),
            ),
        )
        assert result2.decision == PolicyDecision.NO_DECISION


class TestConsentVariants:
    def test_not_opt_in(self):
        policies = [
            ParsedPolicy(
                key="allow-unless",
                priority=100,
                decision=PolicyDecision.ALLOW,
                unless=[
                    {
                        "type": "consent",
                        "privacy_notice_key": "n",
                        "requirement": "not_opt_in",
                    }
                ],
            ),
        ]
        result = evaluate_policies(policies, req(context={"consent": {"n": "opt_out"}}))
        assert result.decision == PolicyDecision.DENY

        result2 = evaluate_policies(policies, req(context={"consent": {"n": "opt_in"}}))
        assert result2.decision == PolicyDecision.ALLOW

    def test_not_opt_out(self):
        policies = [
            ParsedPolicy(
                key="allow-unless",
                priority=100,
                decision=PolicyDecision.ALLOW,
                unless=[
                    {
                        "type": "consent",
                        "privacy_notice_key": "n",
                        "requirement": "not_opt_out",
                    }
                ],
            ),
        ]
        result = evaluate_policies(policies, req(context={"consent": {"n": "opt_in"}}))
        assert result.decision == PolicyDecision.DENY

        result2 = evaluate_policies(
            policies, req(context={"consent": {"n": "opt_out"}})
        )
        assert result2.decision == PolicyDecision.ALLOW


class TestGeoNotIn:
    def test_not_in_operator(self):
        policies = [
            ParsedPolicy(
                key="deny-unless-outside",
                priority=100,
                decision=PolicyDecision.DENY,
                unless=[
                    {
                        "type": "geo_location",
                        "field": "environment.geo_location",
                        "operator": "not_in",
                        "values": ["US-CA"],
                    }
                ],
            ),
        ]
        result = evaluate_policies(
            policies, req(context={"environment": {"geo_location": "US-CA"}})
        )
        assert result.decision == PolicyDecision.DENY

        result2 = evaluate_policies(
            policies, req(context={"environment": {"geo_location": "EU-DE"}})
        )
        assert result2.decision == PolicyDecision.NO_DECISION


class TestDataFlowNoneOf:
    def test_none_of_operator(self):
        policies = [
            ParsedPolicy(
                key="allow-unless",
                priority=100,
                decision=PolicyDecision.ALLOW,
                unless=[
                    {
                        "type": "data_flow",
                        "direction": "egress",
                        "operator": "none_of",
                        "systems": ["trusted_partner"],
                    }
                ],
            ),
        ]
        result = evaluate_policies(
            policies, req(context={"data_flows": {"egress": ["trusted_partner"]}})
        )
        assert result.decision == PolicyDecision.ALLOW

        result2 = evaluate_policies(
            policies, req(context={"data_flows": {"egress": ["unknown_vendor"]}})
        )
        assert result2.decision == PolicyDecision.DENY


class TestEdgeCases:
    def test_no_context_unless_does_not_trigger(self):
        policies = [
            ParsedPolicy(
                key="allow-unless",
                priority=100,
                decision=PolicyDecision.ALLOW,
                unless=[
                    {
                        "type": "consent",
                        "privacy_notice_key": "x",
                        "requirement": "opt_out",
                    }
                ],
            ),
        ]
        result = evaluate_policies(policies, req())
        assert result.decision == PolicyDecision.ALLOW

    def test_deny_action_only_on_deny(self):
        policies = [
            ParsedPolicy(
                key="allow-with-action",
                priority=100,
                decision=PolicyDecision.ALLOW,
                action=PolicyAction(message="should not appear"),
            ),
        ]
        result = evaluate_policies(policies, req())
        assert result.decision == PolicyDecision.ALLOW
        assert result.action is None

    def test_empty_match_catches_everything(self):
        policies = [
            ParsedPolicy(key="catch-all", priority=1, decision=PolicyDecision.DENY)
        ]
        result = evaluate_policies(policies, req())
        assert result.decision == PolicyDecision.DENY

    def test_context_nested_field_resolution(self):
        policies = [
            ParsedPolicy(
                key="deny-unless-nested",
                priority=100,
                decision=PolicyDecision.DENY,
                unless=[
                    {
                        "type": "geo_location",
                        "field": "a.b.c",
                        "operator": "in",
                        "values": ["deep_value"],
                    }
                ],
            ),
        ]
        result = evaluate_policies(
            policies, req(context={"a": {"b": {"c": "deep_value"}}})
        )
        assert result.decision == PolicyDecision.NO_DECISION

    def test_taxonomy_empty_key_never_matches(self):
        policies = [
            ParsedPolicy(
                key="empty-key",
                priority=100,
                decision=PolicyDecision.DENY,
                match={"data_use": {"any": [""]}},
            ),
        ]
        result = evaluate_policies(policies, req(data_uses=("marketing",)))
        assert result.decision == PolicyDecision.NO_DECISION

    def test_enabled_defaults_to_true(self):
        policies = [
            ParsedPolicy(
                key="default-enabled", priority=100, decision=PolicyDecision.DENY
            )
        ]
        result = evaluate_policies(policies, req())
        assert result.decision == PolicyDecision.DENY

    def test_duplicate_unless_constraints(self):
        policies = [
            ParsedPolicy(
                key="allow-unless-dup",
                priority=100,
                decision=PolicyDecision.ALLOW,
                unless=[
                    {
                        "type": "consent",
                        "privacy_notice_key": "n",
                        "requirement": "opt_out",
                    },
                    {
                        "type": "consent",
                        "privacy_notice_key": "n",
                        "requirement": "opt_out",
                    },
                ],
            ),
        ]
        result = evaluate_policies(policies, req(context={"consent": {"n": "opt_out"}}))
        assert result.decision == PolicyDecision.DENY

        result2 = evaluate_policies(policies, req(context={"consent": {"n": "opt_in"}}))
        assert result2.decision == PolicyDecision.ALLOW

    def test_match_dimension_both_any_and_all(self):
        policies = [
            ParsedPolicy(
                key="both-ops",
                priority=100,
                decision=PolicyDecision.DENY,
                match={
                    "data_category": {
                        "any": ["user.contact", "user.financial"],
                        "all": ["user.contact", "user.financial"],
                    }
                },
            ),
        ]
        result = evaluate_policies(
            policies,
            req(data_categories=("user.contact.email", "user.financial.bank_account")),
        )
        assert result.decision == PolicyDecision.DENY

        result2 = evaluate_policies(
            policies, req(data_categories=("user.contact.email",))
        )
        assert result2.decision == PolicyDecision.NO_DECISION

    def test_priority_tie_preserves_insertion_order(self):
        """Stable sort: policies at the same priority keep their original order."""
        policies = [
            ParsedPolicy(
                key="first-allow", priority=100, decision=PolicyDecision.ALLOW
            ),
            ParsedPolicy(key="second-deny", priority=100, decision=PolicyDecision.DENY),
        ]
        result = evaluate_policies(policies, req())
        assert result.decision == PolicyDecision.ALLOW
        assert result.decisive_policy_key == "first-allow"


class TestProtocolConformance:
    def test_evaluator_conforms_to_protocol(self):
        evaluator = InProcessAccessPolicyEvaluator(
            policies=[
                ParsedPolicy(key="deny-all", priority=0, decision=PolicyDecision.DENY)
            ]
        )
        result = evaluator.evaluate(req())
        assert result.decision == PolicyDecision.DENY

    def test_evaluator_set_policies(self):
        evaluator = InProcessAccessPolicyEvaluator()
        result = evaluator.evaluate(req())
        assert result.decision == PolicyDecision.NO_DECISION

        evaluator.set_policies(
            [ParsedPolicy(key="deny-all", priority=0, decision=PolicyDecision.DENY)]
        )
        result = evaluator.evaluate(req())
        assert result.decision == PolicyDecision.DENY


class TestJsonConversion:
    def test_parsed_policy_from_dict(self):
        p = parsed_policy_from_dict(
            {
                "key": "test",
                "priority": 50,
                "enabled": False,
                "decision": "ALLOW",
                "match": {"data_use": {"any": ["marketing"]}},
                "action": {"message": "hello"},
            }
        )
        assert p.key == "test"
        assert p.priority == 50
        assert p.enabled is False
        assert p.decision == PolicyDecision.ALLOW
        assert p.action is not None
        assert p.action.message == "hello"

    def test_parsed_policy_from_dict_defaults(self):
        p = parsed_policy_from_dict({})
        assert p.key == ""
        assert p.enabled is True
        assert p.decision == PolicyDecision.DENY

    def test_request_from_dict(self):
        r = request_from_dict(
            {
                "consumer_id": "c1",
                "data_uses": ["marketing"],
                "context": {"consent": {"n": "opt_out"}},
            }
        )
        assert r.consumer_id == "c1"
        assert r.data_uses == ("marketing",)
        assert r.context == {"consent": {"n": "opt_out"}}

    def test_result_round_trip(self):
        policies = [
            ParsedPolicy(
                key="deny-all",
                priority=0,
                decision=PolicyDecision.DENY,
                action=PolicyAction(message="denied"),
            )
        ]
        result = evaluate_policies(policies, req())
        d = result_to_dict(result)
        assert d["decision"] == "DENY"
        assert d["decisive_policy_key"] == "deny-all"
        assert d["action"]["message"] == "denied"
        assert len(d["evaluated_policies"]) == 1
