# pylint: disable=missing-docstring, redefined-outer-name
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from fideslang.models import (
    DataCategory,
    Dataset,
    DatasetCollection,
    DataSubject,
    DataUse,
    MatchesEnum,
    Policy,
    PolicyRule,
    PrivacyDeclaration,
    System,
    Taxonomy,
)

from fides.config import FidesConfig
from fides.core import evaluate


# Helpers
@pytest.fixture()
def evaluation_key_validation_basic_taxonomy() -> Taxonomy:
    yield Taxonomy(
        data_subject=[
            DataSubject(fides_key="data_subject_1"),
            DataSubject(fides_key="data_subject_2"),
        ],
        data_category=[
            DataCategory(fides_key="data_category_1"),
            DataCategory(fides_key="data_category_2"),
        ],
        data_use=[DataUse(fides_key="data_use_1"), DataUse(fides_key="data_use_2")],
    )


@pytest.fixture()
def evaluation_hierarchical_key_basic_taxonomy() -> Taxonomy:
    yield Taxonomy(
        data_category=[
            DataCategory(
                fides_key="data_category",
            ),
            DataCategory(
                fides_key="data_category.parent",
                parent_key="data_category",
            ),
            DataCategory(
                fides_key="data_category.parent.child",
                parent_key="data_category.parent",
            ),
        ]
    )


def create_policy_rule_with_keys(
    data_categories: List[str],
    data_uses: List[str],
    data_subjects: List[str],
) -> PolicyRule:
    return PolicyRule(
        name="policy_rule_1",
        data_categories={
            "values": data_categories,
            "matches": MatchesEnum.ANY,
        },
        data_uses={
            "values": data_uses,
            "matches": MatchesEnum.ANY,
        },
        data_subjects={
            "values": data_subjects,
            "matches": MatchesEnum.ANY,
        },
    )


@pytest.mark.integration
def test_get_all_server_policies(test_config: FidesConfig) -> None:
    result = evaluate.get_all_server_policies(
        url=test_config.cli.server_url, headers=test_config.user.auth_header
    )
    assert len(result) > 0


@pytest.mark.integration
def test_populate_referenced_keys_recursively(test_config: FidesConfig) -> None:
    """
    Test that populate_referenced_keys works recursively. It should be able to
    find the keys in the declaration and also populate any keys which those reference.
    For instance, a category would reference a new resource in its parent_key but it would
    not be known until that category was populated first.
    """
    result_taxonomy = evaluate.populate_referenced_keys(
        taxonomy=Taxonomy(
            system=[
                System(
                    fides_key="test_system",
                    system_type="test",
                    privacy_declarations=[
                        PrivacyDeclaration(
                            name="privacy_declaration_1",
                            data_categories=["user.contact.email"],
                            data_use="essential.service",
                            data_subjects=["customer"],
                        )
                    ],
                )
            ],
        ),
        url=test_config.cli.server_url,
        headers=test_config.user.auth_header,
        last_keys=[],
    )

    populated_categories = [
        category.fides_key for category in result_taxonomy.data_category
    ]
    assert sorted(populated_categories) == sorted(
        ["user.contact.email", "user.contact", "user"]
    )

    populated_data_uses = [data_use.fides_key for data_use in result_taxonomy.data_use]
    assert sorted(populated_data_uses) == sorted(["essential.service", "essential"])

    populated_subjects = [
        data_subject.fides_key for data_subject in result_taxonomy.data_subject
    ]
    assert sorted(populated_subjects) == sorted(["customer"])


@pytest.mark.integration
def test_populate_referenced_keys_fails_missing_keys(
    test_config: FidesConfig,
) -> None:
    """
    Test that populate_referenced_keys will fail if missing keys
    are referenced in taxonomy
    """
    with pytest.raises(SystemExit):
        evaluate.populate_referenced_keys(
            taxonomy=Taxonomy(
                system=[
                    System(
                        fides_key="test_system",
                        system_type="test",
                        privacy_declarations=[
                            PrivacyDeclaration(
                                name="privacy_declaration_1",
                                data_categories=["missing.category"],
                                data_use="essential.service",
                                data_subjects=["customer"],
                            )
                        ],
                    )
                ],
            ),
            url=test_config.cli.server_url,
            headers=test_config.user.auth_header,
            last_keys=[],
        )


@pytest.mark.integration
def test_hydrate_missing_resources(test_config: FidesConfig) -> None:
    dehydrated_taxonomy = Taxonomy(
        data_category=[
            DataCategory(
                name="test_dc",
                fides_key="key_1.test_dc",
                description="test description",
                parent_key="key_1",
            ),
        ],
        system=[
            System.model_construct(
                name="test_dc",
                fides_key="test_dc",
                description="test description",
                egress=[{"fides_key": "key_3"}, {"fides_key": "key_4"}],
                system_type="test",
                privacy_declarations=None,
            )
        ],
    )
    actual_hydrated_taxonomy = evaluate.hydrate_missing_resources(
        url=test_config.cli.server_url,
        headers=test_config.user.auth_header,
        dehydrated_taxonomy=dehydrated_taxonomy,
        missing_resource_keys={
            "user.authorization.credentials",
            "user",
        },
    )
    assert len(actual_hydrated_taxonomy.data_category) == 3


@pytest.mark.unit
def test_get_evaluation_policies_with_key_found_local() -> None:
    """
    Test that when a fides key is supplied the local policy is returned when found
    """
    server_policy = Policy(fides_key="fides_key_1", rules=[])
    local_policy_1 = Policy(fides_key="fides_key_1", rules=[])
    local_policy_2 = Policy(fides_key="fides_key_2", rules=[])
    get_server_resource_mock = MagicMock(return_value=server_policy)
    with patch("fides.core.evaluate.get_server_resource", get_server_resource_mock):
        policies = evaluate.get_evaluation_policies(
            local_policies=[local_policy_1, local_policy_2],
            evaluate_fides_key="fides_key_1",
            url="url",
            headers={},
        )

    assert len(policies) == 1
    assert policies[0] is local_policy_1


@pytest.mark.unit
def test_get_evaluation_policies_with_key_found_remote() -> None:
    """
    Test that when a fides key is supplied and not found locally, it will be
    fetched from the server
    """
    server_policy = Policy(fides_key="fides_key_1", rules=[])
    local_policy = Policy(fides_key="fides_key_2", rules=[])
    get_server_resource_mock = MagicMock(return_value=server_policy)
    with patch("fides.core.evaluate.get_server_resource", get_server_resource_mock):
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
def test_get_evaluation_policies_with_no_key(test_config: FidesConfig) -> None:
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
        "fides.core.evaluate.get_all_server_policies",
        get_all_server_policies_mock,
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
def test_validate_policies_exist_throws_with_empty() -> None:
    with pytest.raises(SystemExit):
        evaluate.validate_policies_exist(policies=[], evaluate_fides_key="fides_key")


@pytest.mark.unit
def test_validate_policies_exist_with_policies() -> None:
    evaluate.validate_policies_exist(
        policies=[Policy(fides_key="fides_key_1", rules=[])],
        evaluate_fides_key="fides_key",
    )


@pytest.mark.unit
def test_compare_rule_to_declaration_any_true() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_1"]],
        rule_match="ANY",
    )
    assert {"key_1"} == result


@pytest.mark.unit
def test_compare_rule_to_declaration_any_true_hierarchical() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1_parent"],
        declaration_type_hierarchies=[["key_2"], ["key_1", "key_1_parent"]],
        rule_match="ANY",
    )
    assert {"key_1"} == result


@pytest.mark.unit
def test_compare_rule_to_declaration_any_false() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_3"]],
        rule_match="ANY",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_any_false_hierarchical() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2", "key_2_parent"], ["key_3"]],
        rule_match="ANY",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_true() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_3"],
        declaration_type_hierarchies=[["key_3"], ["key_1"]],
        rule_match="ALL",
    )
    assert {"key_3", "key_1"} == result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_true_hierarchical() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1_parent", "key_3_parent"],
        declaration_type_hierarchies=[
            ["key_3", "key_3_parent"],
            ["key_1", "key_1_parent"],
        ],
        rule_match="ALL",
    )
    assert {"key_3", "key_1"} == result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_false() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_3"],
        declaration_type_hierarchies=[["key_2"], ["key_1"]],
        rule_match="ALL",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_all_false_hierarchical() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_1_parent", "key_3"],
        declaration_type_hierarchies=[["key_2"], ["key_1", "key_1_parent"]],
        rule_match="ALL",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_true() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_3"]],
        rule_match="NONE",
    )
    assert {"key_2", "key_3"} == result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_true_hierarchical() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2", "key_2_parent"], ["key_3"]],
        rule_match="NONE",
    )
    assert {"key_2", "key_3"} == result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_false() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_3"], ["key_1"]],
        rule_match="NONE",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_none_false_hierarchical() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1_parent"],
        declaration_type_hierarchies=[["key_2"], ["key_3"], ["key_1", "key_1_parent"]],
        rule_match="NONE",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_other_true() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1"],
        declaration_type_hierarchies=[["key_2"], ["key_1"]],
        rule_match="OTHER",
    )
    assert {"key_2"} == result


@pytest.mark.unit
def test_compare_rule_to_declaration_other_true_hierarchical() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1_parent"],
        declaration_type_hierarchies=[["key_2"], ["key_1", "key_1_parent"]],
        rule_match="OTHER",
    )
    assert {"key_2"} == result


@pytest.mark.unit
def test_compare_rule_to_declaration_other_false() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_3"],
        declaration_type_hierarchies=[["key_1"], ["key_3"]],
        rule_match="OTHER",
    )
    assert not result


@pytest.mark.unit
def test_compare_rule_to_declaration_other_false_hierarchical() -> None:
    result = evaluate.compare_rule_to_declaration(
        rule_types=["key_1", "key_3_parent"],
        declaration_type_hierarchies=[["key_1"], ["key_3", "key_3_parent"]],
        rule_match="OTHER",
    )
    assert not result


@pytest.mark.unit
def test_get_dataset_by_fides_key_exists() -> None:
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
def test_get_dataset_by_fides_key_does_not_exist() -> None:
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
def test_get_fides_key_parent_hierarchy_child(
    evaluation_hierarchical_key_basic_taxonomy: Taxonomy,
) -> None:
    result = evaluate.get_fides_key_parent_hierarchy(
        taxonomy=evaluation_hierarchical_key_basic_taxonomy,
        fides_key="data_category.parent.child",
    )
    assert result == [
        "data_category.parent.child",
        "data_category.parent",
        "data_category",
    ]


@pytest.mark.unit
def test_get_fides_key_parent_hierarchy_parent(
    evaluation_hierarchical_key_basic_taxonomy: Taxonomy,
) -> None:
    result = evaluate.get_fides_key_parent_hierarchy(
        taxonomy=evaluation_hierarchical_key_basic_taxonomy,
        fides_key="data_category.parent",
    )
    assert result == ["data_category.parent", "data_category"]


@pytest.mark.unit
def test_get_fides_key_parent_hierarchy_top_level(
    evaluation_hierarchical_key_basic_taxonomy: Taxonomy,
) -> None:
    result = evaluate.get_fides_key_parent_hierarchy(
        taxonomy=evaluation_hierarchical_key_basic_taxonomy, fides_key="data_category"
    )
    assert result == ["data_category"]


@pytest.mark.unit
def test_get_fides_key_parent_hierarchy_missing_key(
    evaluation_hierarchical_key_basic_taxonomy: Taxonomy,
) -> None:
    with pytest.raises(SystemExit):
        evaluate.get_fides_key_parent_hierarchy(
            taxonomy=evaluation_hierarchical_key_basic_taxonomy,
            fides_key="data_category.invalid",
        )


@pytest.mark.unit
def test_get_fides_key_parent_hierarchy_missing_parent() -> None:
    with pytest.raises(SystemExit):
        evaluate.get_fides_key_parent_hierarchy(
            taxonomy=Taxonomy(
                data_category=[
                    DataCategory(
                        fides_key="data_category.parent",
                        parent_key="data_category",
                    ),
                ]
            ),
            fides_key="data_category.parent",
        )


@pytest.mark.unit
def test_failed_evaluation_error_message(
    test_config: FidesConfig, capsys: pytest.CaptureFixture
) -> None:
    """
    Check that the returned error message matches what is expected.

    Due to fides_keys being randomized here, we want to check that
    the violations specifically are in the output.
    """
    string_cleaner = lambda x: x.replace("\n", "").replace("\t", "").replace(" ", "")
    expected_error_message = string_cleaner(
        """
  'message': '',
  'status': 'FAIL',
  'violations': [ { 'detail': 'Declaration (Share Political Opinions) of '
                              'system (customer_data_sharing_system) failed '
                              'rule (reject_targeted_marketing) from policy '
                              '(primary_privacy_policy). Violated usage of '
                              'data categories '
                              '(user.demographic.political_opinion) for data'
                              'uses (marketing.advertising.third_party) and'
                              'subjects (customer)',
                    'violating_attributes': { 'data_categories': [ 'user.demographic.political_opinion'],
                                              'data_subjects': ['customer'],
                                              'data_uses': [ 'marketing.advertising.third_party']}}]}
                                              """
    )
    with pytest.raises(SystemExit):
        evaluate.evaluate(
            url=test_config.cli.server_url,
            manifests_dir="tests/ctl/data/failing_declaration_taxonomy.yml",
            headers=test_config.user.auth_header,
            local=True,
        )
    captured_out = string_cleaner(capsys.readouterr().out)
    print(f"Expected output:\n{expected_error_message}")
    print(f"Captured output:\n{captured_out}")
    assert captured_out.endswith(expected_error_message)


@pytest.mark.unit
class TestMergeTaxonomies:
    def test_no_key_conflicts(self) -> None:
        taxonomy_1 = Taxonomy(data_subject=[DataSubject(fides_key="foo", name="bar")])
        taxonomy_2 = Taxonomy(data_subject=[DataSubject(fides_key="bar", name="baz")])
        taxonomy_3 = Taxonomy(
            data_subject=[
                DataSubject(fides_key="foo", name="bar"),
                DataSubject(fides_key="bar", name="baz"),
            ]
        )
        assert evaluate.merge_taxonomies(taxonomy_1, taxonomy_2) == taxonomy_3

    def test_key_conflicts(self) -> None:
        taxonomy_1 = Taxonomy(data_subject=[DataSubject(fides_key="foo", name="bar")])
        taxonomy_2 = Taxonomy(data_subject=[DataSubject(fides_key="foo", name="baz")])
        taxonomy_3 = Taxonomy(
            data_subject=[
                DataSubject(fides_key="foo", name="bar"),
            ]
        )
        assert evaluate.merge_taxonomies(taxonomy_1, taxonomy_2) == taxonomy_3

    def test_no_same_resources(self) -> None:
        taxonomy_1 = Taxonomy(data_subject=[DataSubject(fides_key="foo", name="bar")])
        taxonomy_2 = Taxonomy(data_category=[DataCategory(fides_key="foo", name="bar")])
        taxonomy_3 = Taxonomy(
            data_subject=[
                DataSubject(fides_key="foo", name="bar"),
            ],
            data_category=[
                DataCategory(fides_key="foo", name="bar"),
            ],
        )
        assert evaluate.merge_taxonomies(taxonomy_1, taxonomy_2) == taxonomy_3
