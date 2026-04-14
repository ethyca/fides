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
            {
                "key": "disabled",
                "priority": 100,
                "enabled": False,
                "decision": "DENY",
                "match": {},
            },
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
        result = evaluate_access_policies(policies, {"data_categories": ["user_data"]})
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
        assert len(result["evaluated_policies"]) == 2
        assert result["evaluated_policies"][0]["result"] == "SUPPRESSED"
        assert result["evaluated_policies"][1]["result"] == "ALLOW"


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
        result1 = evaluate_access_policies(
            policies,
            {
                "context": {
                    "consent": {"do_not_sell": "opt_out"},
                    "environment": {"geo_location": "US-NY"},
                },
            },
        )
        assert result1["decision"] == "ALLOW"

        # Both trigger → DENY
        result2 = evaluate_access_policies(
            policies,
            {
                "context": {
                    "consent": {"do_not_sell": "opt_out"},
                    "environment": {"geo_location": "US-CA"},
                },
            },
        )
        assert result2["decision"] == "DENY"


class TestMatchDataSubject:
    def test_data_subject_matches(self):
        policies = [
            {
                "key": "deny-employee",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {"data_subject": {"any": ["employee"]}},
            },
        ]
        result = evaluate_access_policies(policies, {"data_subjects": ["employee"]})
        assert result["decision"] == "DENY"

    def test_data_subject_no_match(self):
        policies = [
            {
                "key": "deny-employee",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {"data_subject": {"any": ["employee"]}},
            },
        ]
        result = evaluate_access_policies(policies, {"data_subjects": ["customer"]})
        assert result["decision"] == "NO_DECISION"

    def test_three_dimensions_all_must_match(self):
        policies = [
            {
                "key": "specific",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {
                    "data_use": {"any": ["marketing"]},
                    "data_category": {"any": ["user.contact"]},
                    "data_subject": {"any": ["customer"]},
                },
            },
        ]
        # All three match
        result = evaluate_access_policies(
            policies,
            {
                "data_uses": ["marketing.advertising"],
                "data_categories": ["user.contact.email"],
                "data_subjects": ["customer"],
            },
        )
        assert result["decision"] == "DENY"

        # Subject doesn't match
        result2 = evaluate_access_policies(
            policies,
            {
                "data_uses": ["marketing.advertising"],
                "data_categories": ["user.contact.email"],
                "data_subjects": ["employee"],
            },
        )
        assert result2["decision"] == "NO_DECISION"


class TestMatchCombined:
    def test_any_and_all_on_different_dimensions(self):
        policies = [
            {
                "key": "combined",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {
                    "data_use": {"any": ["marketing"]},
                    "data_category": {"all": ["user.contact", "user.financial"]},
                },
            },
        ]
        # Both categories present → match
        result = evaluate_access_policies(
            policies,
            {
                "data_uses": ["marketing.advertising"],
                "data_categories": [
                    "user.contact.email",
                    "user.financial.bank_account",
                ],
            },
        )
        assert result["decision"] == "DENY"

        # Only one category → no match
        result2 = evaluate_access_policies(
            policies,
            {
                "data_uses": ["marketing.advertising"],
                "data_categories": ["user.contact.email"],
            },
        )
        assert result2["decision"] == "NO_DECISION"


class TestConsentVariants:
    def test_not_opt_in(self):
        policies = [
            {
                "key": "allow-unless",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
                "unless": [
                    {
                        "type": "consent",
                        "privacy_notice_key": "n",
                        "requirement": "not_opt_in",
                    },
                ],
            },
        ]
        # opt_out → not_opt_in is true → DENY
        result = evaluate_access_policies(
            policies, {"context": {"consent": {"n": "opt_out"}}}
        )
        assert result["decision"] == "DENY"

        # opt_in → not_opt_in is false → ALLOW
        result2 = evaluate_access_policies(
            policies, {"context": {"consent": {"n": "opt_in"}}}
        )
        assert result2["decision"] == "ALLOW"

    def test_not_opt_out(self):
        policies = [
            {
                "key": "allow-unless",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
                "unless": [
                    {
                        "type": "consent",
                        "privacy_notice_key": "n",
                        "requirement": "not_opt_out",
                    },
                ],
            },
        ]
        # opt_in → not_opt_out is true → DENY
        result = evaluate_access_policies(
            policies, {"context": {"consent": {"n": "opt_in"}}}
        )
        assert result["decision"] == "DENY"

        # opt_out → not_opt_out is false → ALLOW
        result2 = evaluate_access_policies(
            policies, {"context": {"consent": {"n": "opt_out"}}}
        )
        assert result2["decision"] == "ALLOW"


class TestGeoNotIn:
    def test_not_in_operator(self):
        policies = [
            {
                "key": "deny-unless-outside",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {},
                "unless": [
                    {
                        "type": "geo_location",
                        "field": "environment.geo_location",
                        "operator": "not_in",
                        "values": ["US-CA"],
                    }
                ],
            },
        ]
        # In CA → not_in false → unless doesn't trigger → DENY
        result = evaluate_access_policies(
            policies,
            {
                "context": {"environment": {"geo_location": "US-CA"}},
            },
        )
        assert result["decision"] == "DENY"

        # In DE → not_in true → unless triggers → DENY suppressed → NO_DECISION
        result2 = evaluate_access_policies(
            policies,
            {
                "context": {"environment": {"geo_location": "EU-DE"}},
            },
        )
        assert result2["decision"] == "NO_DECISION"


class TestDataFlowNoneOf:
    def test_none_of_operator(self):
        policies = [
            {
                "key": "allow-unless",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
                "unless": [
                    {
                        "type": "data_flow",
                        "direction": "egress",
                        "operator": "none_of",
                        "systems": ["trusted_partner"],
                    }
                ],
            },
        ]
        # trusted_partner present → none_of false → ALLOW
        result = evaluate_access_policies(
            policies,
            {
                "context": {"data_flows": {"egress": ["trusted_partner"]}},
            },
        )
        assert result["decision"] == "ALLOW"

        # trusted_partner absent → none_of true → DENY
        result2 = evaluate_access_policies(
            policies,
            {
                "context": {"data_flows": {"egress": ["unknown_vendor"]}},
            },
        )
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
                    {
                        "type": "consent",
                        "privacy_notice_key": "x",
                        "requirement": "opt_out",
                    }
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
            {
                "key": "catch-all",
                "priority": 1,
                "enabled": True,
                "decision": "DENY",
                "match": {},
            },
        ]
        result = evaluate_access_policies(policies, {})
        assert result["decision"] == "DENY"

    def test_context_nested_field_resolution(self):
        policies = [
            {
                "key": "deny-unless-nested",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {},
                "unless": [
                    {
                        "type": "geo_location",
                        "field": "a.b.c",
                        "operator": "in",
                        "values": ["deep_value"],
                    }
                ],
            },
        ]
        result = evaluate_access_policies(
            policies,
            {
                "context": {"a": {"b": {"c": "deep_value"}}},
            },
        )
        # Unless triggers → DENY suppressed → NO_DECISION
        assert result["decision"] == "NO_DECISION"

    def test_taxonomy_empty_key_never_matches(self):
        policies = [
            {
                "key": "empty-key",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {"data_use": {"any": [""]}},
            },
        ]
        result = evaluate_access_policies(policies, {"data_uses": ["marketing"]})
        assert result["decision"] == "NO_DECISION"

    def test_enabled_defaults_to_true(self):
        # Policy without "enabled" field should be treated as active
        policies = [
            {"key": "no-enabled", "priority": 100, "decision": "DENY", "match": {}},
        ]
        result = evaluate_access_policies(policies, {})
        assert result["decision"] == "DENY"

    def test_duplicate_unless_constraints(self):
        policies = [
            {
                "key": "allow-unless-dup",
                "priority": 100,
                "enabled": True,
                "decision": "ALLOW",
                "match": {},
                "unless": [
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
            },
        ]
        # Both trigger → DENY
        result = evaluate_access_policies(
            policies, {"context": {"consent": {"n": "opt_out"}}}
        )
        assert result["decision"] == "DENY"

        # Neither triggers → ALLOW
        result2 = evaluate_access_policies(
            policies, {"context": {"consent": {"n": "opt_in"}}}
        )
        assert result2["decision"] == "ALLOW"

    def test_match_dimension_both_any_and_all(self):
        policies = [
            {
                "key": "both-ops",
                "priority": 100,
                "enabled": True,
                "decision": "DENY",
                "match": {
                    "data_category": {
                        "any": ["user.contact", "user.financial"],
                        "all": ["user.contact", "user.financial"],
                    }
                },
            },
        ]
        # Both satisfied
        result = evaluate_access_policies(
            policies,
            {"data_categories": ["user.contact.email", "user.financial.bank_account"]},
        )
        assert result["decision"] == "DENY"

        # Any satisfied but not all
        result2 = evaluate_access_policies(
            policies, {"data_categories": ["user.contact.email"]}
        )
        assert result2["decision"] == "NO_DECISION"
