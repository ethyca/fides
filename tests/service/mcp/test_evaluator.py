from unittest.mock import patch

from fides.service.mcp.evaluator import MCPEvaluator
from fides.service.mcp.models import DecisionOutcome, EvaluationInput


def _fake_libpbac_allow(*args, **kwargs):
    return {
        "decision": "ALLOW",
        "decisive_policy_key": "allow_support",
        "action_message": None,
        "evaluated_policies": [
            {"policy_key": "allow_support", "priority": 100, "matched": True,
             "result": "ALLOW", "unless_triggered": False},
        ],
    }


def _fake_libpbac_deny(*args, **kwargs):
    return {
        "decision": "DENY",
        "decisive_policy_key": "block_financial",
        "action_message": "Financial data requires consent",
        "evaluated_policies": [
            {"policy_key": "block_financial", "priority": 200, "matched": True,
             "result": "DENY", "unless_triggered": False},
        ],
    }


def _input():
    return EvaluationInput(
        consumer_fides_key="acme_support",
        data_use="essential.service.operations.support",
        data_categories=["user.contact.email"],
        data_subject="customer",
        environment={"geo_location": "US-CA"},
    )


def test_evaluator_passes_allow_through():
    with patch("fides.service.mcp.evaluator._call_libpbac", _fake_libpbac_allow):
        d = MCPEvaluator(policies_loader=lambda: []).evaluate(_input())
    assert d.decision == DecisionOutcome.ALLOW
    assert d.decisive_policy_key == "allow_support"


def test_evaluator_passes_deny_with_message():
    with patch("fides.service.mcp.evaluator._call_libpbac", _fake_libpbac_deny):
        d = MCPEvaluator(policies_loader=lambda: []).evaluate(_input())
    assert d.decision == DecisionOutcome.DENY
    assert d.action_message == "Financial data requires consent"


def test_evaluator_returns_no_decision_when_no_match():
    no_match = {
        "decision": "NO_DECISION", "decisive_policy_key": None,
        "action_message": None, "evaluated_policies": [],
    }
    with patch("fides.service.mcp.evaluator._call_libpbac", lambda *a, **k: no_match):
        d = MCPEvaluator(policies_loader=lambda: []).evaluate(_input())
    assert d.decision == DecisionOutcome.NO_DECISION
