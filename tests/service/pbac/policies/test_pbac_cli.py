"""Tests for the fides pbac CLI commands.

Uses Click's CliRunner to invoke the commands directly without
needing a running server or Go sidecar.
"""

import json
import os
import tempfile

import pytest
from click.testing import CliRunner

from fides.cli.commands.pbac import pbac


@pytest.fixture
def runner():
    return CliRunner()


class TestEvaluatePurposeCLI:
    def test_compliant_via_stdin(self, runner):
        input_json = json.dumps(
            {
                "consumer": {
                    "consumer_id": "c1",
                    "consumer_name": "Billing",
                    "purpose_keys": ["billing"],
                },
                "datasets": {
                    "billing_db": {
                        "dataset_key": "billing_db",
                        "purpose_keys": ["billing"],
                    },
                },
            }
        )

        result = runner.invoke(pbac, ["evaluate-purpose"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["violations"] == []
        assert output["total_accesses"] == 1

    def test_violation_via_stdin(self, runner):
        input_json = json.dumps(
            {
                "consumer": {
                    "consumer_id": "c1",
                    "consumer_name": "Analytics",
                    "purpose_keys": ["analytics"],
                },
                "datasets": {
                    "billing_db": {
                        "dataset_key": "billing_db",
                        "purpose_keys": ["billing"],
                    },
                },
            }
        )

        result = runner.invoke(pbac, ["evaluate-purpose"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert len(output["violations"]) == 1
        assert output["violations"][0]["dataset_key"] == "billing_db"

    def test_gap_no_consumer_purposes(self, runner):
        input_json = json.dumps(
            {
                "consumer": {
                    "consumer_id": "c1",
                    "consumer_name": "Unknown",
                    "purpose_keys": [],
                },
                "datasets": {
                    "db1": {"dataset_key": "db1", "purpose_keys": ["billing"]},
                },
            }
        )

        result = runner.invoke(pbac, ["evaluate-purpose"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert len(output["gaps"]) == 1
        assert output["gaps"][0]["gap_type"] == "unresolved_identity"

    def test_with_collections(self, runner):
        input_json = json.dumps(
            {
                "consumer": {
                    "consumer_id": "c1",
                    "consumer_name": "Accountant",
                    "purpose_keys": ["accounting"],
                },
                "datasets": {
                    "billing_db": {
                        "dataset_key": "billing_db",
                        "purpose_keys": ["billing"],
                        "collection_purposes": {"invoices": ["accounting"]},
                    },
                },
                "collections": {"billing_db": ["invoices"]},
            }
        )

        result = runner.invoke(pbac, ["evaluate-purpose"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["violations"] == []

    def test_from_file(self, runner):
        data = {
            "consumer": {
                "consumer_id": "c1",
                "consumer_name": "Test",
                "purpose_keys": ["analytics"],
            },
            "datasets": {
                "db1": {"dataset_key": "db1", "purpose_keys": ["analytics"]},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            tmppath = f.name

        try:
            result = runner.invoke(pbac, ["evaluate-purpose", tmppath])
            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["violations"] == []
        finally:
            os.unlink(tmppath)

    def test_multiple_datasets(self, runner):
        input_json = json.dumps(
            {
                "consumer": {
                    "consumer_id": "c1",
                    "consumer_name": "Analyst",
                    "purpose_keys": ["analytics"],
                },
                "datasets": {
                    "analytics_db": {
                        "dataset_key": "analytics_db",
                        "purpose_keys": ["analytics"],
                    },
                    "billing_db": {
                        "dataset_key": "billing_db",
                        "purpose_keys": ["billing"],
                    },
                    "empty_db": {"dataset_key": "empty_db", "purpose_keys": []},
                },
            }
        )

        result = runner.invoke(pbac, ["evaluate-purpose"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["total_accesses"] == 3
        assert len(output["violations"]) == 1
        assert len(output["gaps"]) == 1

    def test_invalid_json(self, runner):
        result = runner.invoke(pbac, ["evaluate-purpose"], input="not json")
        assert result.exit_code != 0

    def test_output_is_valid_json(self, runner):
        input_json = json.dumps(
            {
                "consumer": {
                    "consumer_id": "c1",
                    "consumer_name": "T",
                    "purpose_keys": ["x"],
                },
                "datasets": {"d1": {"dataset_key": "d1", "purpose_keys": ["y"]}},
            }
        )
        result = runner.invoke(pbac, ["evaluate-purpose"], input=input_json)
        assert result.exit_code == 0
        json.loads(result.output)  # should not raise


class TestEvaluatePoliciesCLI:
    def test_allow(self, runner):
        input_json = json.dumps(
            {
                "policies": [
                    {
                        "key": "allow-marketing",
                        "priority": 100,
                        "enabled": True,
                        "decision": "ALLOW",
                        "match": {"data_use": {"any": ["marketing"]}},
                    },
                ],
                "request": {
                    "consumer_id": "c1",
                    "consumer_name": "Marketing",
                    "data_uses": ["marketing.advertising"],
                },
            }
        )

        result = runner.invoke(pbac, ["evaluate-policies"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["decision"] == "ALLOW"
        assert output["decisive_policy_key"] == "allow-marketing"

    def test_deny_with_action(self, runner):
        input_json = json.dumps(
            {
                "policies": [
                    {
                        "key": "deny-all",
                        "priority": 0,
                        "enabled": True,
                        "decision": "DENY",
                        "match": {},
                        "action": {"message": "Access denied"},
                    },
                ],
                "request": {"consumer_id": "c1", "consumer_name": "Anyone"},
            }
        )

        result = runner.invoke(pbac, ["evaluate-policies"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["decision"] == "DENY"
        assert output["action"]["message"] == "Access denied"

    def test_no_decision(self, runner):
        input_json = json.dumps(
            {
                "policies": [],
                "request": {"consumer_id": "c1", "consumer_name": "Test"},
            }
        )

        result = runner.invoke(pbac, ["evaluate-policies"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["decision"] == "NO_DECISION"

    def test_unless_inverts(self, runner):
        input_json = json.dumps(
            {
                "policies": [
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
                ],
                "request": {
                    "data_uses": ["marketing.advertising"],
                    "context": {"consent": {"do_not_sell": "opt_out"}},
                },
            }
        )

        result = runner.invoke(pbac, ["evaluate-policies"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["decision"] == "DENY"
        assert output["unless_triggered"] is True

    def test_priority_ordering(self, runner):
        input_json = json.dumps(
            {
                "policies": [
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
                    },
                ],
                "request": {"data_uses": ["marketing"]},
            }
        )

        result = runner.invoke(pbac, ["evaluate-policies"], input=input_json)

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["decision"] == "DENY"
        assert output["decisive_policy_key"] == "high-deny"

    def test_invalid_json(self, runner):
        result = runner.invoke(pbac, ["evaluate-policies"], input="bad json")
        assert result.exit_code != 0


class TestPbacGroupHelp:
    def test_help(self, runner):
        result = runner.invoke(pbac, ["--help"])
        assert result.exit_code == 0
        assert "evaluate-purpose" in result.output
        assert "evaluate-policies" in result.output
