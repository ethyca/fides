import pytest

from fidesctl.core import evaluate
from fideslang import Taxonomy, System, Policy


@pytest.mark.integration
def test_get_all_server_policies(test_config):
    result = evaluate.get_all_server_policies(
        url=test_config.cli.server_url, headers=test_config.user.request_headers
    )
    assert len(result) > 0


@pytest.mark.unit
def test_compare_rule_to_declaration_any_true():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"], declaration_types=["key_2", "key_1"], rule_inclusion="ANY"
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_any_false():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"], declaration_types=["key_2", "key_3"], rule_inclusion="ANY"
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_true():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_3"],
        declaration_types=["key_3", "key_1"],
        rule_inclusion="ALL",
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_false():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_3"],
        declaration_types=["key_2", "key_1"],
        rule_inclusion="ALL",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_true():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_types=["key_2", "key_3"],
        rule_inclusion="NONE",
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_false():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_types=["key_2", "key_3", "key_1"],
        rule_inclusion="NONE",
    )
    assert not result


@pytest.mark.integration
def test_execute_evaluation_pass():
    assert True


@pytest.mark.integration
def test_execute_evaluation_fail():
    assert True
