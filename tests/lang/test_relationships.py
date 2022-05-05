# pylint: disable=missing-docstring, redefined-outer-name
import pytest

from fidesctl.core.config import FidesctlConfig
from fideslang import relationships
from fideslang.models import (
    DataCategory,
    Dataset,
    DatasetCollection,
    DatasetField,
    MatchesEnum,
    Policy,
    PolicyRule,
    PrivacyDeclaration,
    System,
    Taxonomy,
)


@pytest.mark.unit
def test_find_referenced_fides_keys_1() -> None:
    test_data_category = DataCategory(
        name="test_dc",
        fides_key="key_1.test_dc",
        description="test description",
        parent_key="key_1",
    )
    expected_referenced_key = {"key_1", "key_1.test_dc", "default_organization"}
    referenced_keys = relationships.find_referenced_fides_keys(test_data_category)
    assert referenced_keys == set(expected_referenced_key)


@pytest.mark.unit
def test_find_referenced_fides_keys_2() -> None:
    test_system = System.construct(
        name="test_dc",
        fides_key="test_dc",
        description="test description",
        system_dependencies=["key_1", "key_2"],
        system_type="test",
        privacy_declarations=None,
    )
    expected_referenced_key = {"key_1", "key_2", "test_dc", "default_organization"}
    referenced_keys = relationships.find_referenced_fides_keys(test_system)
    assert referenced_keys == set(expected_referenced_key)


@pytest.mark.unit
def test_get_referenced_missing_keys() -> None:
    taxonomy = Taxonomy(
        data_category=[
            DataCategory(
                name="test_dc",
                fides_key="key_1.test_dc",
                description="test description",
                parent_key="key_1",
            ),
            DataCategory(
                name="test_dc2",
                fides_key="key_1.test_dc2",
                description="test description",
                parent_key="key_1",
            ),
        ],
        system=[
            System.construct(
                name="test_system",
                fides_key="test_system",
                description="test description",
                system_dependencies=["key_3", "key_4"],
                system_type="test",
                privacy_declarations=None,
            )
        ],
    )
    expected_referenced_key = {"key_1", "key_3", "key_4", "default_organization"}
    referenced_keys = relationships.get_referenced_missing_keys(taxonomy)
    assert sorted(referenced_keys) == sorted(set(expected_referenced_key))


@pytest.mark.unit
def test_get_referenced_missing_privacy_declaration_keys() -> None:
    taxonomy = Taxonomy(
        system=[
            System(
                fides_key="system_1",
                system_type="system_type_1",
                privacy_declarations=[
                    PrivacyDeclaration(
                        name="privacy_declaration_1",
                        data_categories=["privacy_declaration_data_category_1"],
                        data_use="privacy_declaration_data_use_1",
                        data_qualifier="privacy_declaration_data_qualifier_1",
                        data_subjects=["privacy_declaration_data_subject_1"],
                        dataset_references=["privacy_declaration_data_set_1"],
                    )
                ],
            )
        ]
    )
    expected_referenced_key = {
        "default_organization",
        "privacy_declaration_data_category_1",
        "privacy_declaration_data_use_1",
        "privacy_declaration_data_qualifier_1",
        "privacy_declaration_data_subject_1",
        "privacy_declaration_data_set_1",
    }
    referenced_keys = relationships.get_referenced_missing_keys(taxonomy)
    assert sorted(referenced_keys) == sorted(set(expected_referenced_key))


@pytest.mark.unit
def test_get_referenced_missing_policy_keys() -> None:
    taxonomy = Taxonomy(
        policy=[
            Policy(
                fides_key="policy_1",
                rules=[
                    PolicyRule(
                        name="policy_rule_1",
                        data_categories={
                            "values": ["policy_rule_data_category_1"],
                            "matches": MatchesEnum.ANY,
                        },
                        data_uses={
                            "values": ["policy_rule_data_use_1"],
                            "matches": MatchesEnum.ANY,
                        },
                        data_subjects={
                            "values": ["policy_rule_data_subject_1"],
                            "matches": MatchesEnum.ANY,
                        },
                        data_qualifier="policy_rule_data_qualifier_1",
                    )
                ],
            )
        ],
    )
    expected_referenced_key = {
        "default_organization",
        "policy_rule_data_category_1",
        "policy_rule_data_use_1",
        "policy_rule_data_subject_1",
        "policy_rule_data_qualifier_1",
    }
    referenced_keys = relationships.get_referenced_missing_keys(taxonomy)
    assert sorted(referenced_keys) == sorted(set(expected_referenced_key))


@pytest.mark.unit
def test_get_referenced_missing_dataset_keys() -> None:
    taxonomy = Taxonomy(
        dataset=[
            Dataset(
                fides_key="dataset_1",
                data_qualifier="dataset_qualifier_1",
                data_categories=["dataset_data_category_1"],
                collections=[
                    DatasetCollection(
                        name="dataset_collection_1",
                        data_qualifier="data_collection_data_qualifier_1",
                        data_categories=["dataset_collection_data_category_1"],
                        fields=[
                            DatasetField(
                                name="dataset_field_1",
                                data_categories=["dataset_field_data_category_1"],
                                data_qualifier="dataset_field_data_qualifier_1",
                            )
                        ],
                    )
                ],
            )
        ],
    )
    expected_referenced_key = {
        "default_organization",
        "dataset_qualifier_1",
        "dataset_data_category_1",
        "data_collection_data_qualifier_1",
        "dataset_collection_data_category_1",
        "dataset_field_data_category_1",
        "dataset_field_data_qualifier_1",
    }
    referenced_keys = relationships.get_referenced_missing_keys(taxonomy)
    assert sorted(referenced_keys) == sorted(set(expected_referenced_key))


@pytest.mark.integration
def test_hydrate_missing_resources(test_config: FidesctlConfig) -> None:
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
            System.construct(
                name="test_dc",
                fides_key="test_dc",
                description="test description",
                system_dependencies=["key_3", "key_4"],
                system_type="test",
                privacy_declarations=None,
            )
        ],
    )
    actual_hydrated_taxonomy = relationships.hydrate_missing_resources(
        url=test_config.cli.server_url,
        headers=test_config.user.request_headers,
        dehydrated_taxonomy=dehydrated_taxonomy,
        missing_resource_keys={
            "user.provided.identifiable.credentials",
            "user.provided",
        },
    )
    assert len(actual_hydrated_taxonomy.data_category) == 3
