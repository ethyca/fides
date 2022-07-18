import pytest

from fidesops.common_exceptions import FidesopsException
from fidesops.graph.config import (
    Collection,
    Dataset,
    FieldAddress,
    FieldPath,
    ObjectField,
    ScalarField,
)
from fidesops.util.saas_util import assign_placeholders, merge_datasets, unflatten_dict


class TestMergeDatasets:
    """
    Multiple scenarios for merging SaaS config references with SaaS datasets.

    SaaS datasets will not contain references and serve only as a definition
    of available data from the given SaaS connector. Any references to other datasets
    will be provided by the SaaS config.
    """

    def test_add_identity(self):
        """Augment a SaaS dataset collection with an identity reference"""

        saas_dataset = Dataset(
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

        saas_config = Dataset(
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

    @pytest.mark.unit_saas
    def test_add_reference(self):
        """Augment a SaaS dataset collection with a dataset reference"""

        saas_dataset = Dataset(
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

        saas_config = Dataset(
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

    @pytest.mark.unit_saas
    def test_add_with_object_fields(self):
        """Verify complex SaaS dataset fields are preserved after merging"""
        saas_dataset = Dataset(
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

        saas_config = Dataset(
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

    @pytest.mark.unit_saas
    def test_merge_same_scalar_field(self):
        """Merge two scalar fields between datsets with the same collection/field name"""
        saas_dataset = Dataset(
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

        saas_config = Dataset(
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

    @pytest.mark.unit_saas
    def test_merge_same_object_field(self):
        """Merge a scalar and object field between datsets with the same collection/field name"""
        saas_dataset = Dataset(
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

        saas_config = Dataset(
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


def test_unflatten_dict():
    # empty dictionary
    assert unflatten_dict({}) == {}

    # empty dictionary value
    assert unflatten_dict({"A": {}}) == {"A": {}}

    # unflattened dictionary
    assert unflatten_dict({"A": "1"}) == {"A": "1"}

    # same level
    assert unflatten_dict({"A.B": "1", "A.C": "2"}) == {"A": {"B": "1", "C": "2"}}

    # mixed levels
    assert unflatten_dict({"A": "1", "B.C": "2", "B.D": "3",}) == {
        "A": "1",
        "B": {"C": "2", "D": "3"},
    }

    # long path
    assert unflatten_dict({"A.B.C.D.E.F.G": "1"}) == {
        "A": {"B": {"C": {"D": {"E": {"F": {"G": "1"}}}}}}
    }

    # incoming values should overwrite existing values
    assert unflatten_dict({"A.B": 1, "A.B": 2}) == {"A": {"B": 2}}

    # conflicting types
    with pytest.raises(FidesopsException):
        unflatten_dict({"A.B": 1, "A": 2, "A.C": 3})

    # data passed in is not completely flattened
    with pytest.raises(FidesopsException):
        unflatten_dict({"A.B.C": 1, "A": {"B.D": 2}})

    # unflatten_dict shouldn't be called with a None separator
    with pytest.raises(IndexError):
        unflatten_dict({"": "1"}, separator=None)
