import pytest

from fideslang import relationships, DataCategory, System, Taxonomy


@pytest.mark.unit
def test_find_referenced_fides_keys_1():
    test_data_category = DataCategory(
        name="test_dc",
        fides_key="key_1.test_dc",
        description="test description",
        parent_key="key_1",
    )
    expected_referenced_key = {"key_1", "key_1.test_dc"}
    referenced_keys = relationships.find_referenced_fides_keys(test_data_category)
    assert referenced_keys == set(expected_referenced_key)


@pytest.mark.unit
def test_find_referenced_fides_keys_2():
    test_system = System.construct(
        name="test_dc",
        fides_key="test_dc",
        description="test description",
        system_dependencies=["key_1", "key_2"],
        system_type="test",
        privacy_declarations=None,
    )
    expected_referenced_key = {"key_1", "key_2", "test_dc"}
    referenced_keys = relationships.find_referenced_fides_keys(test_system)
    assert referenced_keys == set(expected_referenced_key)


@pytest.mark.unit
def test_get_referenced_missing_keys():
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
    expected_referenced_key = {"key_1", "key_3", "key_4"}
    referenced_keys = relationships.get_referenced_missing_keys(taxonomy)
    assert sorted(referenced_keys) == sorted(set(expected_referenced_key))


@pytest.mark.integration
def test_hydrate_missing_resources(test_config):
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
        missing_resource_keys={"user.provided.identifiable.credentials", "user.provided"},
    )
    assert len(actual_hydrated_taxonomy.data_category) == 3


@pytest.mark.integration
def test_hydrate_missing_resources_fail(test_config):
    with pytest.raises(SystemExit):
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
        relationships.hydrate_missing_resources(
            url=test_config.cli.server_url,
            headers=test_config.user.request_headers,
            dehydrated_taxonomy=dehydrated_taxonomy,
            missing_resource_keys={"non_existent_key", "key_3"},
        )
    assert True
