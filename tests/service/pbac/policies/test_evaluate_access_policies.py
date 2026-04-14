"""Tests for the Access Policy v2 evaluation engine (Python implementation).

These mirror the Go tests in policy-engine/pkg/pbac/policy_evaluate_test.go
to ensure both implementations produce identical results.
"""

import pytest

from fides.service.pbac.policies.evaluate import evaluate_access_policies


class TestPriorityOrdering:
    def test_highest_priority_wins(self):
        policies = [
            {
                "key": "low-allow",
                "priority": 10,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
            },
            {
                "key": "high-deny",
                "priority": 200,
                "enabled": True,
                "decision": "DENY",
                "match": {},
                "action": {"message": "Highest priority wins"},
            },
        ]
        request = {"data_uses": ["marketing"]}

        result = evaluate_access_policies(policies, request)

        assert result["decision"] == "DENY"
        assert result["decisive_policy_key"] == "high-deny"

    def test_allow_when_matched(self):
        policies = [
            {
                "key": "deny-financial",
                "priority": 200,
                "enabled": True,
                "decision": "DENY",
                "match": {"data_category": {"any": ["user.financial"]}},
            },
            {
                "key": "allow-marketing",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {"data_use": {"any": ["marketing"]}},
            },
        ]
        request = {
            "data_uses": ["marketing.advertising"],
            "data_categories": ["user.contact.email"],
        }

        result = evaluate_access_policies(policies, request)

        assert result["decision"] == "ALLOW"
        assert result["decisive_policy_key"] == "allow-marketing"

    def test_catch_all_deny(self):
        policies = [
            {
                "key": "catch-all",
                "priority": 0,
                "enabled": True,
                "decision": "DENY",
                "match": {},
                "action": {"message": "Default deny"},
            },
        ]

        result = evaluate_access_policies(policies, {"data_uses": ["essential"]})

        assert result["decision"] == "DENY"
        assert result["decisive_policy_key"] == "catch-all"
        assert result["action"]["message"] == "Default deny"


class TestNoDecision:
    def test_empty_policies(self):
        result = evaluate_access_policies([], {})
        assert result["decision"] == "NO_DECISION"

    def test_disabled_policies_skipped(self):
        policies = [
            {"key": "disabled", "priority": 100, "enabled": False, "decision": "DENY", "match": {}},
        ]
        result = evaluate_access_policies(policies, {})
        assert result["decision"] == "NO_DECISION"

    def test_no_match(self):
        policies = [
            {
                "key": "deny-financial",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {"data_category": {"any": ["user.financial"]}},
            },
        ]
        result = evaluate_access_policies(
            policies, {"data_categories": ["system.operations"]}
        )
        assert result["decision"] == "NO_DECISION"


class TestTaxonomyMatching:
    def test_parent_matches_child(self):
        policies = [
            {
                "key": "deny-user",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {"data_category": {"any": ["user"]}},
            },
        ]
        result = evaluate_access_policies(
            policies, {"data_categories": ["user.contact.email"]}
        )
        assert result["decision"] == "DENY"

    def test_child_does_not_match_parent(self):
        policies = [
            {
                "key": "deny-child",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {"data_category": {"any": ["user.contact.email"]}},
            },
        ]
        result = evaluate_access_policies(
            policies, {"data_categories": ["user.contact"]}
        )
        assert result["decision"] == "NO_DECISION"

    def test_no_dot_boundary_false_positive(self):
        policies = [
            {
                "key": "deny-user",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {"data_category": {"any": ["user"]}},
            },
        ]
        result = evaluate_access_policies(
            policies, {"data_categories": ["user_data"]}
        )
        assert result["decision"] == "NO_DECISION"

    def test_match_all_requires_every_value(self):
        policies = [
            {
                "key": "require-both",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {
                    "data_category": {
                        "all": ["user.contact", "user.financial"],
                    }
                },
            },
        ]

        # Only one → no match
        result1 = evaluate_access_policies(
            policies, {"data_categories": ["user.contact.email"]}
        )
        assert result1["decision"] == "NO_DECISION"

        # Both → match
        result2 = evaluate_access_policies(
            policies,
            {"data_categories": ["user.contact.email", "user.financial.bank_account"]},
        )
        assert result2["decision"] == "DENY"


class TestUnlessConsent:
    def test_opt_out_inverts_allow(self):
        policies = [
            {
                "key": "allow-unless-optout",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {"data_use": {"any": ["marketing"]}},
                "unless": [
                    {
                        "type": "consent",
                        "privacy_notice_key": "do_not_sell",
                        "requirement": "opt_out",
                    }
                ],
                "action": {"message": "User opted out"},
            },
        ]
        request = {
            "data_uses": ["marketing.advertising"],
            "context": {"consent": {"do_not_sell": "opt_out"}},
        }

        result = evaluate_access_policies(policies, request)

        assert result["decision"] == "DENY"
        assert result["unless_triggered"] is True

    def test_consent_not_triggered_allow_stands(self):
        policies = [
            {
                "key": "allow-unless-optout",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {"data_use": {"any": ["marketing"]}},
                "unless": [
                    {
                        "type": "consent",
                        "privacy_notice_key": "do_not_sell",
                        "requirement": "opt_out",
                    }
                ],
            },
        ]
        request = {
            "data_uses": ["marketing.advertising"],
            "context": {"consent": {"do_not_sell": "opt_in"}},
        }

        result = evaluate_access_policies(policies, request)
        assert result["decision"] == "ALLOW"
        assert result["unless_triggered"] is False


class TestUnlessGeo:
    def test_deny_suppressed_continues_to_next(self):
        policies = [
            {
                "key": "deny-unless-geo",
                "priority": 200,
                "enabled": True,
                "decision": "DENY",
                "match": {},
                "unless": [
                    {
                        "type": "geo_location",
                        "field": "environment.geo_location",
                        "operator": "in",
                        "values": ["US-CA"],
                    }
                ],
            },
            {
                "key": "fallback-allow",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
            },
        ]
        request = {
            "context": {"environment": {"geo_location": "US-CA"}},
        }

        result = evaluate_access_policies(policies, request)

        assert result["decision"] == "ALLOW"
        assert result["decisive_policy_key"] == "fallback-allow"
        assert len(result["evaluated_policies"]) == 1
        assert result["evaluated_policies"][0]["result"] == "SUPPRESSED"


class TestUnlessDataFlow:
    def test_egress_triggers_unless(self):
        policies = [
            {
                "key": "allow-unless-egress",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
                "unless": [
                    {
                        "type": "data_flow",
                        "direction": "egress",
                        "operator": "any_of",
                        "systems": ["external_vendor"],
                    }
                ],
            },
        ]
        request = {
            "context": {
                "data_flows": {"egress": ["external_vendor", "partner_api"]},
            },
        }

        result = evaluate_access_policies(policies, request)
        assert result["decision"] == "DENY"


class TestUnlessMultipleConstraints:
    def test_all_must_trigger(self):
        policies = [
            {
                "key": "allow-unless-both",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
                "unless": [
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
            },
        ]

        # Only consent triggers → ALLOW stands
        result1 = evaluate_access_policies(policies, {
            "context": {
                "consent": {"do_not_sell": "opt_out"},
                "environment": {"geo_location": "US-NY"},
            },
        })
        assert result1["decision"] == "ALLOW"

        # Both trigger → DENY
        result2 = evaluate_access_policies(policies, {
            "context": {
                "consent": {"do_not_sell": "opt_out"},
                "environment": {"geo_location": "US-CA"},
            },
        })
        assert result2["decision"] == "DENY"


class TestEdgeCases:
    def test_no_context_unless_does_not_trigger(self):
        policies = [
            {
                "key": "allow-unless",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
                "unless": [
                    {"type": "consent", "privacy_notice_key": "x", "requirement": "opt_out"}
                ],
            },
        ]
        result = evaluate_access_policies(policies, {})
        assert result["decision"] == "ALLOW"

    def test_deny_action_only_on_deny(self):
        policies = [
            {
                "key": "allow-with-action",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
                "action": {"message": "should not appear"},
            },
        ]
        result = evaluate_access_policies(policies, {})
        assert result["decision"] == "ALLOW"
        assert result.get("action") is None

    def test_empty_match_catches_everything(self):
        policies = [
            {"key": "catch-all", "priority": 1, "enabled": True, "decision": "DENY", "match": {}},
        ]
        result = evaluate_access_policies(policies, {})
        assert result["decision"] == "DENY"
