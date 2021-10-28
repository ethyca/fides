from unittest.mock import patch, MagicMock
import pytest

from fidesctl.core import evaluate

from fideslang.models import (
    DataCategory,
    DataQualifier,
    DataSubject,
    DataUse,
    Dataset,
    DatasetCollection,
    Policy,
    Taxonomy,
)


# Helpers
@pytest.fixture()
def evaluation_key_validation_taxonomy():
    yield Taxonomy(
        data_subject=[
            DataSubject(fides_key="data_subject_1"),
            DataSubject(fides_key="data_subject_2"),
        ],
        data_category=[
            DataCategory(fides_key="data_category_1"),
            DataCategory(fides_key="data_category_2"),
        ],
        data_qualifier=[
            DataQualifier(fides_key="data_qualifier_1"),
            DataQualifier(fides_key="data_qualifier_2"),
        ],
        data_use=[DataUse(fides_key="data_use_1"), DataUse(fides_key="data_use_2")],
    )


@pytest.mark.integration
def test_get_all_server_policies(test_config):
    result = evaluate.get_all_server_policies(
        url=test_config.cli.server_url, headers=test_config.user.request_headers
    )
    assert len(result) > 0


@pytest.mark.unit
def test_get_evaluation_policies_with_key_found_local():
    """
    Test that when a fides key is supplied the local policy is returned when found
    """
    server_policy = Policy(fides_key="fides_key_1", rules=[])
    local_policy_1 = Policy(fides_key="fides_key_1", rules=[])
    local_policy_2 = Policy(fides_key="fides_key_2", rules=[])
    get_server_resource_mock = MagicMock(return_value=server_policy)
    with patch("fidesctl.core.evaluate.get_server_resource", get_server_resource_mock):
        policies = evaluate.get_evaluation_policies(
            local_policies=[local_policy_1, local_policy_2],
            evaluate_fides_key="fides_key_1",
            url="url",
            headers={},
        )

    assert len(policies) == 1
    assert policies[0] is local_policy_1


@pytest.mark.unit
def test_get_evaluation_policies_with_key_found_remote():
    """
    Test that when a fides key is supplied and not found locally, it will be
    fetched from the server
    """
    server_policy = Policy(fides_key="fides_key_1", rules=[])
    local_policy = Policy(fides_key="fides_key_2", rules=[])
    get_server_resource_mock = MagicMock(return_value=server_policy)
    with patch("fidesctl.core.evaluate.get_server_resource", get_server_resource_mock):
        policies = evaluate.get_evaluation_policies(
            local_policies=[local_policy],
            evaluate_fides_key="fides_key_1",
            url="url",
            headers={},
        )

    assert len(policies) == 1
    assert policies[0] is server_policy
    get_server_resource_mock.assert_called_with(
        url="url", resource_type="policy", resource_key="fides_key_1", headers={}
    )


@pytest.mark.unit
def test_get_evaluation_policies_with_no_key(test_config):
    """
    Test that when no fides key is supplied all local and server policies are
    returned.
    """
    server_policy_1 = Policy(fides_key="fides_key_1", rules=[])
    server_policy_2 = Policy(fides_key="fides_key_2", rules=[])
    local_policy_1 = Policy(fides_key="fides_key_3", rules=[])
    local_policy_2 = Policy(fides_key="fides_key_4", rules=[])
    get_all_server_policies_mock = MagicMock(
        return_value=[server_policy_1, server_policy_2]
    )
    with patch(
        "fidesctl.core.evaluate.get_all_server_policies", get_all_server_policies_mock
    ):
        policies = evaluate.get_evaluation_policies(
            local_policies=[local_policy_1, local_policy_2],
            evaluate_fides_key="",
            url="url",
            headers={},
        )

    assert len(policies) == 4
    get_all_server_policies_mock.assert_called_with(
        url="url", headers={}, exclude=["fides_key_3", "fides_key_4"]
    )


@pytest.mark.unit
def test_validate_policies_exist_throws_with_empty():
    with pytest.raises(SystemExit):
        evaluate.validate_policies_exist(policies=[], evaluate_fides_key="fides_key")


@pytest.mark.unit
def test_validate_policies_exist_with_policies():
    evaluate.validate_policies_exist(
        policies=[Policy(fides_key="fides_key_1", rules=[])],
        evaluate_fides_key="fides_key",
    )


@pytest.mark.unit
def test_compare_rule_to_declaration_any_true():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_1"]],
        rule_inclusion="ANY",
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_any_true_hierarchical():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1_parent"],
        declaration_type_hierarchies=[["key_2"], ["key_1", "key_1_parent"]],
        rule_inclusion="ANY",
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_any_false():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_3"]],
        rule_inclusion="ANY",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_any_false_hierarchical():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2", "key_2_parent"], ["key_3"]],
        rule_inclusion="ANY",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_true():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_3"],
        declaration_type_hierarchies=[["key_3"], ["key_1"]],
        rule_inclusion="ALL",
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_true_hierarchical():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1_parent", "key_3_parent"],
        declaration_type_hierarchies=[
            ["key_3", "key_3_parent"],
            ["key_1", "key_1_parent"],
        ],
        rule_inclusion="ALL",
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_false():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_3"],
        declaration_type_hierarchies=[["key_2"], ["key_1"]],
        rule_inclusion="ALL",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_false_hierarchical():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_1_parent", "key_3"],
        declaration_type_hierarchies=[["key_2"], ["key_1" "key_1_parent"]],
        rule_inclusion="ALL",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_true():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_3"]],
        rule_inclusion="NONE",
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_true_hierarchical():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2", "key_2_parent"], ["key_3"]],
        rule_inclusion="NONE",
    )
    assert result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_false():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_3"], ["key_1"]],
        rule_inclusion="NONE",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_false_hierarchical():
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1_parent"],
        declaration_type_hierarchies=[["key_2"], ["key_3"], ["key_1", "key_1_parent"]],
        rule_inclusion="NONE",
    )
    assert not result


@pytest.mark.unit
def test_get_dataset_by_fides_key_exists():
    dataset_1 = Dataset(
        fides_key="dataset_1", collections=[DatasetCollection(name="", fields=[])]
    )
    dataset_2 = Dataset(
        fides_key="dataset_2", collections=[DatasetCollection(name="", fields=[])]
    )
    result = evaluate.get_dataset_by_fides_key(
        taxonomy=Taxonomy(dataset=[dataset_1, dataset_2]), fides_key="dataset_1"
    )
    assert result == dataset_1


@pytest.mark.unit
def test_get_dataset_by_fides_key_does_not_exist():
    dataset1 = Dataset(
        fides_key="dataset_1", collections=[DatasetCollection(name="", fields=[])]
    )
    dataset_2 = Dataset(
        fides_key="dataset_2", collections=[DatasetCollection(name="", fields=[])]
    )
    result = evaluate.get_dataset_by_fides_key(
        taxonomy=Taxonomy(dataset=[dataset1, dataset_2]), fides_key="dataset_3"
    )
    assert not result


@pytest.mark.unit
def test_validate_fides_keys_exist_for_evaluation_pass(
    evaluation_key_validation_taxonomy,
):
    evaluate.validate_fides_keys_exist_for_evaluation(
        taxonomy=evaluation_key_validation_taxonomy,
        data_subjects=["data_subject_1"],
        data_categories=["data_category_1"],
        data_qualifier="data_qualifier_2",
        data_use="data_use_1",
    )


@pytest.mark.unit
def test_validate_fides_keys_exist_for_evaluation_missing_data_subject(
    evaluation_key_validation_taxonomy,
):
    with pytest.raises(SystemExit):
        evaluate.validate_fides_keys_exist_for_evaluation(
            taxonomy=evaluation_key_validation_taxonomy,
            data_subjects=["data_subject_3"],
            data_categories=["data_category_1"],
            data_qualifier="data_qualifier_2",
            data_use="data_use_1",
        )


@pytest.mark.unit
def test_validate_fides_keys_exist_for_evaluation_missing_data_categrory(
    evaluation_key_validation_taxonomy,
):
    with pytest.raises(SystemExit):
        evaluate.validate_fides_keys_exist_for_evaluation(
            taxonomy=evaluation_key_validation_taxonomy,
            data_subjects=["data_subject_1"],
            data_categories=["data_category_3"],
            data_qualifier="data_qualifier_2",
            data_use="data_use_1",
        )


@pytest.mark.unit
def test_validate_fides_keys_exist_for_evaluation_missing_data_qualifier(
    evaluation_key_validation_taxonomy,
):
    with pytest.raises(SystemExit):
        evaluate.validate_fides_keys_exist_for_evaluation(
            taxonomy=evaluation_key_validation_taxonomy,
            data_subjects=["data_subject_1"],
            data_categories=["data_category_1"],
            data_qualifier="data_qualifier_3",
            data_use="data_use_1",
        )

@pytest.mark.unit
def test_validate_fides_keys_exist_for_evaluation_missing_data_use(
    evaluation_key_validation_taxonomy,
):
    with pytest.raises(SystemExit):
        evaluate.validate_fides_keys_exist_for_evaluation(
            taxonomy=evaluation_key_validation_taxonomy,
            data_subjects=["data_subject_1"],
            data_categories=["data_category_1"],
            data_qualifier="data_qualifier_1",
            data_use="data_use_3",
        )