import pytest

from fides.api.common_exceptions import FidesopsException
from fides.api.graph.config import (
    Collection,
    FieldAddress,
    FieldPath,
    GraphDataset,
    ObjectField,
    ScalarField,
)
from fides.api.util.saas_util import (
    assign_placeholders,
    merge_datasets,
    replace_version,
)


@pytest.mark.unit_saas
class TestMergeDatasets:
    """
    Multiple scenarios for merging SaaS config references with SaaS datasets.

    SaaS datasets will not contain references and serve only as a definition
    of available data from the given SaaS connector. Any references to other datasets
    will be provided by the SaaS config.
    """

    def test_add_identity(self):
        """Augment a SaaS dataset collection with an identity reference"""

        saas_dataset = GraphDataset(
            name="saas_dataset",
            collections=[
                Collection(
                    name="member",
                    fields=[
                        ScalarField(name="list_id"),
                    ],
                )
            ],
            connection_key="connection_key",
        )

        saas_config = GraphDataset(
            name="saas_config",
            collections=[
                Collection(
                    name="member",
                    fields=[
                        ScalarField(name="query", identity="email"),
                    ],
                )
            ],
            connection_key="connection_key",
        )

        merged_dataset = merge_datasets(saas_dataset, saas_config)
        collection = merged_dataset.collections[0]
        assert len(collection.fields) == 2

        list_id_field = collection.top_level_field_dict[FieldPath("list_id")]
        assert len(list_id_field.references) == 0
        query_field = collection.top_level_field_dict[FieldPath("query")]
        assert len(query_field.references) == 0
        assert query_field.identity == "email"

    def test_add_reference(self):
        """Augment a SaaS dataset collection with a dataset reference"""

        saas_dataset = GraphDataset(
            name="saas_dataset",
            collections=[
                Collection(
                    name="conversations",
                    fields=[
                        ScalarField(name="campaign_id"),
                    ],
                )
            ],
            connection_key="connection_key",
        )

        saas_config = GraphDataset(
            name="saas_config",
            collections=[
                Collection(
                    name="conversations",
                    fields=[
                        ScalarField(
                            name="conversation_id",
                            references=[
                                (
                                    FieldAddress(
                                        "saas_connector", "member", "unique_email_id"
                                    ),
                                    "from",
                                )
                            ],
                        ),
                    ],
                )
            ],
            connection_key="connection_key",
        )

        merged_dataset = merge_datasets(saas_dataset, saas_config)
        collection = merged_dataset.collections[0]
        assert len(collection.fields) == 2

        campaign_id_field = collection.top_level_field_dict[FieldPath("campaign_id")]
        assert len(campaign_id_field.references) == 0

        conversation_id_field = collection.top_level_field_dict[
            FieldPath("conversation_id")
        ]
        assert len(conversation_id_field.references) == 1
        assert conversation_id_field.references[0] == (
            FieldAddress("saas_connector", "member", "unique_email_id"),
            "from",
        )

    def test_add_with_object_fields(self):
        """Verify complex SaaS dataset fields are preserved after merging"""
        saas_dataset = GraphDataset(
            name="saas_dataset",
            collections=[
                Collection(
                    name="member",
                    fields=[
                        ObjectField(
                            name="name",
                            fields={
                                "first": ScalarField(name="first"),
                                "last": ScalarField(name="last"),
                            },
                        )
                    ],
                )
            ],
            connection_key="connection_key",
        )

        saas_config = GraphDataset(
            name="saas_config",
            collections=[
                Collection(
                    name="member",
                    fields=[
                        ScalarField(name="query", identity="email"),
                    ],
                )
            ],
            connection_key="connection_key",
        )

        merged_dataset = merge_datasets(saas_dataset, saas_config)
        collection = merged_dataset.collections[0]
        assert len(collection.fields) == 2

        query_field = collection.top_level_field_dict[FieldPath("query")]
        assert len(query_field.references) == 0
        assert query_field.identity == "email"
        name_field = collection.top_level_field_dict[FieldPath("name")]
        assert isinstance(name_field, ObjectField)
        assert len(name_field.fields) == 2

    def test_merge_same_scalar_field(self):
        """Merge two scalar fields between datsets with the same collection/field name"""
        saas_dataset = GraphDataset(
            name="saas_dataset",
            collections=[
                Collection(
                    name="conversations",
                    fields=[
                        ScalarField(name="query"),
                    ],
                )
            ],
            connection_key="connection_key",
        )

        saas_config = GraphDataset(
            name="saas_config",
            collections=[
                Collection(
                    name="conversations",
                    fields=[
                        ScalarField(
                            name="query",
                            references=[
                                (
                                    FieldAddress(
                                        "saas_connector", "member", "unique_email_id"
                                    ),
                                    "from",
                                )
                            ],
                        ),
                    ],
                )
            ],
            connection_key="connection_key",
        )
        merged_dataset = merge_datasets(saas_dataset, saas_config)
        collection = merged_dataset.collections[0]
        assert len(collection.fields) == 1
        assert len(collection.fields[0].references) == 1

    def test_merge_same_object_field(self):
        """Merge a scalar and object field between datsets with the same collection/field name"""
        saas_dataset = GraphDataset(
            name="saas_dataset",
            collections=[
                Collection(
                    name="member",
                    fields=[
                        ObjectField(
                            name="name",
                            fields={
                                "first": ScalarField(name="first"),
                                "last": ScalarField(name="last"),
                            },
                        )
                    ],
                )
            ],
            connection_key="connection_key",
        )

        saas_config = GraphDataset(
            name="saas_config",
            collections=[
                Collection(
                    name="member",
                    fields=[
                        ScalarField(name="name", identity="email"),
                    ],
                )
            ],
            connection_key="connection_key",
        )

        merged_dataset = merge_datasets(saas_dataset, saas_config)
        collection = merged_dataset.collections[0]
        assert len(collection.fields) == 1
        name_field = collection.top_level_field_dict[FieldPath("name")]
        assert isinstance(name_field, ObjectField)
        assert len(name_field.fields) == 2
        assert name_field.identity == "email"

    def test_merge_into_dataset_with_data_categories(self):
        """Verify that the data categories in the target dataset are preserved after merging"""
        saas_dataset = GraphDataset(
            name="saas_dataset",
            collections=[
                Collection(
                    name="member",
                    data_categories={"user"},
                    fields=[
                        ObjectField(
                            name="name",
                            fields={
                                "first": ScalarField(name="first"),
                                "last": ScalarField(name="last"),
                            },
                        )
                    ],
                )
            ],
            connection_key="connection_key",
        )

        saas_config = GraphDataset(
            name="saas_config",
            collections=[
                Collection(
                    name="member",
                    fields=[
                        ScalarField(name="name", identity="email"),
                    ],
                )
            ],
            connection_key="connection_key",
        )

        merged_dataset = merge_datasets(saas_dataset, saas_config)
        assert merged_dataset.collections[0].data_categories == {"user"}


@pytest.mark.unit_saas
class TestAssignPlaceholders:
    def test_string_value(self):
        assert assign_placeholders("domain", {}) == "domain"

    def test_int_value(self):
        assert assign_placeholders(100, {}) == 100

    def test_none_value(self):
        assert assign_placeholders(None, {}) == None

    def test_single_placeholder_with_string_value(self):
        assert assign_placeholders("<access_key>", {"access_key": "123"}) == "123"

    def test_single_placeholder_with_empty_string_value(self):
        assert (
            assign_placeholders(
                "{<masked_object_fields>}", {"masked_object_fields": ""}
            )
            == "{}"
        )

    def test_single_placeholder_with_int_value(self):
        assert assign_placeholders("<page_size>", {"page_size": 10}) == "10"

    def test_multiple_string_placeholders(self):
        assert (
            assign_placeholders("/v1/<org>/<project>", {"org": "abc", "project": "123"})
            == "/v1/abc/123"
        )

    def test_multiple_int_placeholders(self):
        assert (
            assign_placeholders(
                "/user/<user_id>/order/<order_id>", {"user_id": 1, "order_id": 2}
            )
            == "/user/1/order/2"
        )

    def test_multiple_mixed_placeholders(self):
        assert (
            assign_placeholders(
                "/user/<user_id>/order/<order_id>", {"user_id": "abc", "order_id": 1}
            )
            == "/user/abc/order/1"
        )
        assert (
            assign_placeholders(
                "/user/<user_id>/order/<order_id>", {"user_id": 1, "order_id": "abc"}
            )
            == "/user/1/order/abc"
        )

    def test_placeholder_value_not_found(self):
        # we return null if any placeholder cannot be found,
        # we let the caller decide if this is allowed or should be considered an error
        assert assign_placeholders("<access_key>", {}) == None

    def test_second_placeholder_not_found(self):
        # verify that the original value is not mutated if we are only able to do a partial replacement
        value = "/user/<user_id>/order/<order_id>"
        assert assign_placeholders(value, {"user_id": 1}) == None
        assert value == "/user/<user_id>/order/<order_id>"

    def test_regex_is_not_greedy(self):
        assert assign_placeholders("<<access>>", {"access": "letmein"}) == "<letmein>"
        assert assign_placeholders("<access>>>", {"access": "letmein"}) == "letmein>>"
        assert assign_placeholders("<<<access>", {"access": "letmein"}) == "<<letmein"
        assert (
            assign_placeholders(
                "<outer>leaveithere<placeholders>", {"outer": "|", "placeholders": "|"}
            )
            == "|leaveithere|"
        )

    def test_json_string_with_mandatory_placeholder(self):
        json_str = '{"name": "<name>", "age": <age>}'
        assert (
            assign_placeholders(json_str, {"name": "John", "age": 30})
            == '{"name": "John", "age": 30}'
        )

    def test_json_string_with_missing_mandatory_placeholder(self):
        json_str = '{"name": "<name>", "age": <age>}'
        assert assign_placeholders(json_str, {"name": "John"}) is None

    def test_json_string_with_optional_placeholder(self):
        json_str = '{"name": "<name>", "address": "<address?>"}'
        assert (
            assign_placeholders(json_str, {"name": "John"})
            == '{"name": "John", "address": null}'
        )
        assert (
            assign_placeholders(json_str, {"name": "John", "address": "123 Main St"})
            == '{"name": "John", "address": "123 Main St"}'
        )

    def test_json_string_with_mixed_placeholders(self):
        json_str = '{"name": "<name>", "age": <age>, "address": "<address?>"}'
        assert (
            assign_placeholders(json_str, {"name": "John", "age": 30})
            == '{"name": "John", "age": 30, "address": null}'
        )
        assert (
            assign_placeholders(
                json_str, {"name": "John", "age": 30, "address": "123 Main St"}
            )
            == '{"name": "John", "age": 30, "address": "123 Main St"}'
        )

    def test_json_string_with_nested_placeholders(self):
        json_str = '{"user": {"name": "<name>", "age": <age>, "credentials": {"token": "<token?>", "expiry": "<expiry?>"}}}'
        params = {
            "name": "John",
            "age": 30,
            "token": "abc123",
        }
        assert (
            assign_placeholders(json_str, params)
            == '{"user": {"name": "John", "age": 30, "credentials": {"token": "abc123", "expiry": null}}}'
        )

    def test_complex_json_string(self):
        json_str = '{"users": [{"name": "<name1>"}, {"name": "<name2?>"}], "metadata": {"count": <count>}}'
        params = {"name1": "John", "count": 2}
        assert (
            assign_placeholders(json_str, params)
            == '{"users": [{"name": "John"}, {"name": null}], "metadata": {"count": 2}}'
        )

    def test_dot_delimited_placeholder(self):
        assert (
            assign_placeholders(
                '{"user": {"name": "<user.name>"}}', {"user": {"name": "Alice"}}
            )
            == '{"user": {"name": "Alice"}}'
        )

    def test_dot_delimited_placeholder_with_int(self):
        assert (
            assign_placeholders('{"user": {"age": <user.age>}}', {"user": {"age": 30}})
            == '{"user": {"age": 30}}'
        )

    def test_multiple_dot_delimited_placeholders(self):
        assert (
            assign_placeholders(
                '{"user": {"name": "<user.name>", "age": <user.age>}}',
                {"user": {"name": "Bob", "age": 25}},
            )
            == '{"user": {"name": "Bob", "age": 25}}'
        )

    def test_optional_dot_delimited_placeholder_present(self):
        assert (
            assign_placeholders(
                '{"user": {"name": "<user.name?>", "age": <user.age>}}',
                {"user": {"name": "Eve", "age": 28}},
            )
            == '{"user": {"name": "Eve", "age": 28}}'
        )

    def test_optional_dot_delimited_placeholder_missing(self):
        assert (
            assign_placeholders(
                '{"user": {"name": "<user.name?>", "age": <user.age>}}',
                {"user": {"age": 28}},
            )
            == '{"user": {"name": null, "age": 28}}'
        )

    def test_dot_delimited_placeholder_missing(self):
        assert (
            assign_placeholders(
                '{"user": {"name": "<user.name>", "age": <user.age>}}',
                {"user": {"age": 28}},
            )
            is None
        )

    def test_replacing_with_object_values(self):
        assert (
            assign_placeholders(
                "{<all_object_fields>}",
                {"all_object_fields": {"age": 28, "name": "Bob"}},
            )
            == '{"age": 28, "name": "Bob"}'
        )

    def test_replacing_with_string_list_values(self):
        assert (
            assign_placeholders(
                '{"subscriber_ids": <subscriber_ids>}',
                {"subscriber_ids": ["123", "456"]},
            )
            == '{"subscriber_ids": ["123", "456"]}'
        )

    def test_replacing_with_integer_list_values(self):
        assert (
            assign_placeholders(
                '{"account_ids": <account_ids>}',
                {"account_ids": [123, 456]},
            )
            == '{"account_ids": [123, 456]}'
        )

    def test_replacing_with_empty_list_values(self):
        assert (
            assign_placeholders(
                '{"subscriber_ids": <subscriber_ids>}',
                {"subscriber_ids": []},
            )
            == '{"subscriber_ids": []}'
        )


@pytest.mark.unit_saas
class TestUnflattenDict:
    def test_empty_dict(self):
        assert unflatten_dict({}) == {}

    def test_empty_dict_value(self):
        assert unflatten_dict({"A": {}}) == {"A": {}}

    def test_unflattened_dict(self):
        assert unflatten_dict({"A": "1"}) == {"A": "1"}

    def test_same_level(self):
        assert unflatten_dict({"A.B": "1", "A.C": "2"}) == {"A": {"B": "1", "C": "2"}}

    def test_mixed_levels(self):
        assert unflatten_dict(
            {
                "A": "1",
                "B.C": "2",
                "B.D": "3",
            }
        ) == {
            "A": "1",
            "B": {"C": "2", "D": "3"},
        }

    def test_long_path(self):
        assert unflatten_dict({"A.B.C.D.E.F.G": "1"}) == {
            "A": {"B": {"C": {"D": {"E": {"F": {"G": "1"}}}}}}
        }

    def test_single_item_array(self):
        assert unflatten_dict({"A.0.B": "C"}) == {"A": [{"B": "C"}]}

    def test_multi_item_array(self):
        assert unflatten_dict({"A.0.B": "C", "A.1.D": "E"}) == {
            "A": [{"B": "C"}, {"D": "E"}]
        }

    def test_multi_value_array(self):
        assert unflatten_dict(
            {"A.0.B": "C", "A.0.D": "E", "A.1.F": "G", "A.1.H": "I"}
        ) == {"A": [{"B": "C", "D": "E"}, {"F": "G", "H": "I"}]}

    def test_array_with_scalar_value(self):
        assert unflatten_dict({"A.0": "B"}) == {"A": ["B"]}

    def test_array_with_scalar_values(self):
        assert unflatten_dict({"A.0": "B", "A.1": "C"}) == {"A": ["B", "C"]}

    def test_overwrite_existing_values(self):
        assert unflatten_dict({"A.B": 1, "A.B": 2}) == {"A": {"B": 2}}

    def test_conflicting_types(self):
        with pytest.raises(FidesopsException):
            unflatten_dict({"A.B": 1, "A": 2, "A.C": 3})

    def test_mixed_types_in_array(self):
        assert unflatten_dict({"A.0": "B", "A.1.C": "D"}) == {"A": ["B", {"C": "D"}]}

    def test_data_not_completely_flattened(self):
        assert unflatten_dict({"A.B.C": 1, "A": {"B.D": 2}}) == {
            "A": {"B": {"C": 1, "D": 2}}
        }

    def test_response_with_object_fields_specified(self):
        assert unflatten_dict(
            {
                "address.email": "2a3aaa22b2ccce15ef7a1e94ee@email.com",
                "address.name": "MASKED",
                "metadata": {"age": "24", "place": "Bedrock"},
                "return_path": "",
                "substitution_data": {
                    "favorite_color": "SparkPost Orange",
                    "job": "Software Engineer",
                },
                "tags": ["greeting", "prehistoric", "fred", "flintstone"],
            }
        ) == {
            "address": {
                "email": "2a3aaa22b2ccce15ef7a1e94ee@email.com",
                "name": "MASKED",
            },
            "metadata": {"age": "24", "place": "Bedrock"},
            "return_path": "",
            "substitution_data": {
                "favorite_color": "SparkPost Orange",
                "job": "Software Engineer",
            },
            "tags": ["greeting", "prehistoric", "fred", "flintstone"],
        }

    def test_none_separator(self):
        with pytest.raises(IndexError):
            unflatten_dict({"": "1"}, separator=None)


@pytest.mark.unit_saas
class TestReplaceVersion:
    def test_replace_version(self):
        # base case
        assert (
            replace_version("saas_config:\n  version: 0.0.1\n  key: example", "0.0.2")
            == "saas_config:\n  version: 0.0.2\n  key: example"
        )

        # ignore extra spaces
        assert (
            replace_version("saas_config:\n  version:  0.0.1\n  key: example", "0.0.2")
            == "saas_config:\n  version: 0.0.2\n  key: example"
        )

        # version not found
        assert (
            replace_version("saas_config:\n  key: example", "1.0.0")
            == "saas_config:\n  key: example"
        )

        # occurrences of *version: in the rest of the config
        assert (
            replace_version(
                "saas_config:\n  version: 0.0.1\n  key: example\n  other_version: 0.0.2",
                "0.0.3",
            )
            == "saas_config:\n  version: 0.0.3\n  key: example\n  other_version: 0.0.2"
        )
