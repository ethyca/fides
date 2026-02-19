import pytest

from fides.api.graph.config import (
    Collection,
    FieldAddress,
    FieldPath,
    GraphDataset,
    ObjectField,
    ScalarField,
)
from fides.api.schemas.saas.saas_config import ParamValue
from fides.api.util.collection_util import unflatten_dict
from fides.api.util.saas_util import (
    assign_placeholders,
    check_dataset_missing_reference_values,
    find_unresolved_placeholders,
    merge_datasets,
    nullsafe_urlencode,
    replace_version,
    validate_allowed_domains_not_modified,
    validate_domain_against_allowed_list,
    validate_host_references_domain_restricted_params,
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

    def test_none_separator(self):
        with pytest.raises(IndexError):
            unflatten_dict({"": "1"}, separator=None)


@pytest.mark.unit_saas
class TestFindUnresolvedPlaceholders:
    def test_none_value(self):
        assert find_unresolved_placeholders(None, {}) == []

    def test_non_string_value(self):
        assert find_unresolved_placeholders(100, {}) == []

    def test_empty_string(self):
        assert find_unresolved_placeholders("", {}) == []

    def test_no_placeholders(self):
        assert find_unresolved_placeholders("domain", {}) == []

    def test_all_placeholders_resolved(self):
        assert (
            find_unresolved_placeholders(
                "/v1/<org>/<project>", {"org": "abc", "project": "123"}
            )
            == []
        )

    def test_single_unresolved_placeholder(self):
        assert find_unresolved_placeholders("<access_key>", {}) == ["access_key"]

    def test_multiple_unresolved_placeholders(self):
        result = find_unresolved_placeholders("/user/<user_id>/order/<order_id>", {})
        assert "user_id" in result
        assert "order_id" in result
        assert len(result) == 2

    def test_partial_unresolved(self):
        result = find_unresolved_placeholders(
            "/user/<user_id>/order/<order_id>", {"user_id": 1}
        )
        assert result == ["order_id"]

    def test_optional_placeholders_excluded(self):
        assert find_unresolved_placeholders(
            '{"name": "<name?>", "age": <age>}', {}
        ) == ["age"]

    def test_all_optional_placeholders(self):
        assert (
            find_unresolved_placeholders(
                '{"name": "<name?>", "address": "<address?>"}', {}
            )
            == []
        )

    def test_dot_delimited_unresolved(self):
        assert find_unresolved_placeholders(
            '{"user": {"name": "<user.name>"}}', {"user": {"age": 28}}
        ) == ["user.name"]

    def test_dot_delimited_resolved(self):
        assert (
            find_unresolved_placeholders(
                '{"user": {"name": "<user.name>"}}', {"user": {"name": "Alice"}}
            )
            == []
        )


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


@pytest.mark.unit_saas
class TestNullsafeUrlencode:
    """Tests for the nullsafe_urlencode function that handles None values in URL encoding"""

    def test_nullsafe_urlencode_simple_dict(self):
        """Test encoding a simple dictionary with None values"""
        data = {"name": "John", "email": None, "age": 30}
        result = nullsafe_urlencode(data)

        assert "name=John" in result
        assert "email=" in result  # None becomes empty string
        assert "age=30" in result

    def test_nullsafe_urlencode_nested_dict(self):
        """Test encoding a nested dictionary with None values"""
        data = {
            "user": {
                "name": "John",
                "contact": {"email": None, "phone": "123-456-7890"},
            }
        }
        result = nullsafe_urlencode(data)

        assert "user%5Bname%5D=John" in result
        assert "user%5Bcontact%5D%5Bemail%5D=" in result  # None becomes empty string
        assert "user%5Bcontact%5D%5Bphone%5D=123-456-7890" in result

    def test_nullsafe_urlencode_with_list(self):
        """Test encoding data containing lists with None values"""
        data = {"names": ["John", None, "Jane"], "scores": [10, None, 30]}
        result = nullsafe_urlencode(data)

        assert "names%5B%5D=John" in result
        assert "names%5B%5D=" in result  # None becomes empty string
        assert "names%5B%5D=Jane" in result
        assert "scores%5B%5D=10" in result
        assert "scores%5B%5D=" in result  # None becomes empty string
        assert "scores%5B%5D=30" in result

    def test_nullsafe_urlencode_empty_input(self):
        """Test encoding empty or None input"""
        assert nullsafe_urlencode({}) == ""

        # Handle None special case - multidimensional_urlencode requires a dict
        try:
            # This should raise a TypeError because multidimensional_urlencode only supports dicts
            nullsafe_urlencode(None)
            assert False, "Expected TypeError when passing None to nullsafe_urlencode"
        except TypeError:
            # We expect a TypeError, so this is correct behavior
            pass

    def test_nullsafe_urlencode_complex_structure(self):
        """Test encoding a complex nested structure with various None values"""
        data = {
            "user": {
                "name": "John",
                "details": None,
                "addresses": [
                    {"street": "123 Main St", "city": None},
                    None,
                    {"street": None, "city": "Boston"},
                ],
            },
            "settings": None,
        }
        result = nullsafe_urlencode(data)

        # The exact format of the encoded result should contain these parts
        expected_parts = {
            "settings=",
            "user%5Baddresses%5D%5B%5D=%7B%27street%27%3A+%27123+Main+St%27%2C+%27city%27%3A+%27%27%7D",
            "user%5Baddresses%5D%5B%5D=",
            "user%5Baddresses%5D%5B%5D=%7B%27street%27%3A+%27%27%2C+%27city%27%3A+%27Boston%27%7D",
            "user%5Bdetails%5D=",
            "user%5Bname%5D=John",
        }
        result_parts = set(result.split("&"))
        assert result_parts == expected_parts


@pytest.mark.unit_saas
class TestCheckDatasetReferenceValues:
    def test_check_dataset_missing_reference_values_no_values_missing(self):
        """Test that no values are missing when all the reference values are present"""
        input_data = {
            "fidesops_grouped_inputs": [],
            "user_id": ["test_user_123"],
            "email": ["user@example.com"],
            "privacy_request": [
                {
                    "id": "pri_test_request_id",
                    "status": "in_processing",
                    "policy": {
                        "name": "Test Access Policy",
                        "key": "test_access_policy",
                    },
                    "source": "Test Source",
                }
            ],
        }
        param_values = [
            ParamValue(
                name="user_id",
                identity=None,
                references=["customer.user_id"],
                connector_param=None,
                unpack=False,
            ),
            ParamValue(
                name="email",
                identity=None,
                references=["customer.email"],
                connector_param=None,
                unpack=False,
            ),
        ]
        assert check_dataset_missing_reference_values(input_data, param_values) == []

    def test_check_dataset_missing_reference_values_values_missing(self):
        """Test that we identify missing values when some reference values are not present"""
        input_data = {
            "fidesops_grouped_inputs": [],
            "user_id": ["test_user_123"],
            "privacy_request": [
                {"id": "pri_test_request_id", "status": "in_processing"}
            ],
        }
        param_values = [
            ParamValue(
                name="user_id",
                identity=None,
                references=["customer.user_id"],
                connector_param=None,
                unpack=False,
            ),
            ParamValue(
                name="missing_param",
                identity=None,
                references=["customer.missing_field"],
                connector_param=None,
                unpack=False,
            ),
        ]
        assert check_dataset_missing_reference_values(input_data, param_values) == [
            "missing_param"
        ]


@pytest.mark.unit_saas
class TestValidateDomainAgainstAllowedList:
    """Tests for validate_domain_against_allowed_list.

    Each allowed_domains entry is a wildcard pattern where ``*`` matches
    any sequence of characters (including dots).  Everything else is a
    literal.  Matching is case-insensitive against the full domain string.
    """

    @pytest.mark.parametrize(
        "domain,allowed,should_pass",
        [
            pytest.param("api.stripe.com", ["api.stripe.com"], True, id="exact_match"),
            pytest.param(
                "API.Stripe.COM", ["api.stripe.com"], True, id="case_insensitive"
            ),
            pytest.param(
                "  api.stripe.com  ",
                ["  api.stripe.com  "],
                True,
                id="whitespace_stripped",
            ),
            pytest.param(
                "na1.salesforce.com",
                ["*.salesforce.com"],
                True,
                id="wildcard_subdomain",
            ),
            pytest.param(
                "a.b.c.salesforce.com",
                ["*.salesforce.com"],
                True,
                id="wildcard_multi_level",
            ),
            pytest.param(
                "NA1.Salesforce.COM",
                ["*.salesforce.com"],
                True,
                id="wildcard_case_insensitive",
            ),
            pytest.param(
                "api.stripe.com",
                ["api.example.com", "api.stripe.com", "*.other.com"],
                True,
                id="multiple_allowed_domains",
            ),
            pytest.param(
                "sub.other.com",
                ["api.example.com", "api.stripe.com", "*.other.com"],
                True,
                id="multiple_allowed_wildcard",
            ),
            pytest.param(
                "api.us-east.stripe.com",
                ["api.*.stripe.com"],
                True,
                id="wildcard_in_middle",
            ),
            pytest.param(
                "api.us-east.stripe.com",
                ["*.*.stripe.com"],
                True,
                id="multiple_wildcards",
            ),
            pytest.param(
                "salesforce.com",
                ["?*.salesforce.com"],
                False,
                id="question_mark_is_literal_not_regex",
            ),
            pytest.param(
                "evil.example.com", ["api.stripe.com"], False, id="different_domain"
            ),
            pytest.param(
                "not-api.stripe.com",
                ["api.stripe.com"],
                False,
                id="partial_match_rejected",
            ),
            pytest.param(
                "api.stripe.com.evil.com",
                ["api.stripe.com"],
                False,
                id="suffix_attack_rejected",
            ),
        ],
    )
    def test_domain_validation(self, domain, allowed, should_pass):
        if should_pass:
            validate_domain_against_allowed_list(domain, allowed, "domain")
        else:
            with pytest.raises(ValueError):
                validate_domain_against_allowed_list(domain, allowed, "domain")

    def test_error_message_includes_param_name(self):
        """Error message should include the param name and value."""
        with pytest.raises(ValueError, match="The value 'evil.com' for 'domain'"):
            validate_domain_against_allowed_list(
                "evil.com", ["api.stripe.com"], "domain"
            )

    def test_empty_allowed_domains_permits_any_value(self):
        """Empty allowed_domains list should permit any domain value."""
        validate_domain_against_allowed_list(
            "literally-anything.example.com", [], "domain"
        )


@pytest.mark.unit_saas
class TestValidateAllowedDomainsNotModified:
    """Tests for validate_allowed_domains_not_modified (Rule A)."""

    @pytest.mark.parametrize(
        "original,incoming",
        [
            pytest.param(
                [{"name": "domain", "allowed_domains": ["api.stripe.com"]}],
                [{"name": "domain", "allowed_domains": ["api.stripe.com"]}],
                id="identical_allowed_domains",
            ),
            pytest.param(
                [{"name": "api_key"}],
                [{"name": "api_key"}],
                id="no_allowed_domains",
            ),
            pytest.param(
                [
                    {"name": "domain", "allowed_domains": ["api.stripe.com"]},
                    {"name": "extra_param"},
                ],
                [{"name": "domain", "allowed_domains": ["api.stripe.com"]}],
                id="remove_param_without_allowed_domains",
            ),
            pytest.param(
                [{"name": "domain", "allowed_domains": []}],
                [{"name": "domain", "allowed_domains": []}],
                id="empty_list_to_empty_list",
            ),
        ],
    )
    def test_modification_passes(self, original, incoming):
        """Cases where allowed_domains are unchanged or not present."""
        validate_allowed_domains_not_modified(original, incoming)

    @pytest.mark.parametrize(
        "original,incoming,error_match",
        [
            pytest.param(
                [{"name": "domain", "allowed_domains": ["api.stripe.com"]}],
                [{"name": "domain"}],
                "Cannot modify allowed_domains",
                id="remove_allowed_domains",
            ),
            pytest.param(
                [{"name": "domain", "allowed_domains": ["api.stripe.com"]}],
                [{"name": "domain", "allowed_domains": ["evil.com"]}],
                "Cannot modify allowed_domains",
                id="change_allowed_domains_values",
            ),
            pytest.param(
                [{"name": "domain"}],
                [
                    {"name": "domain"},
                    {"name": "new_param", "allowed_domains": ["x.com"]},
                ],
                "Cannot set allowed_domains",
                id="add_allowed_domains_via_api",
            ),
            pytest.param(
                [
                    {"name": "domain", "allowed_domains": ["api.stripe.com"]},
                    {"name": "api_key"},
                ],
                [{"name": "api_key"}],
                "Cannot remove connector param",
                id="remove_param_with_allowed_domains",
            ),
            pytest.param(
                [{"name": "domain", "allowed_domains": []}],
                [{"name": "domain"}],
                "Cannot modify allowed_domains",
                id="empty_list_to_none",
            ),
        ],
    )
    def test_modification_fails(self, original, incoming, error_match):
        """Cases where allowed_domains modification is prohibited."""
        with pytest.raises(ValueError, match=error_match):
            validate_allowed_domains_not_modified(original, incoming)


@pytest.mark.unit_saas
class TestValidateHostReferencesDomainRestrictedParams:
    """Tests for validate_host_references_domain_restricted_params (Rule B)."""

    @staticmethod
    def _make_config(host, endpoints=None, test_request=None):
        """Helper to build a minimal SaaS config dict with client_config.host."""
        config = {"client_config": {"host": host}}
        if endpoints is not None:
            config["endpoints"] = endpoints
        if test_request is not None:
            config["test_request"] = test_request
        return config

    def test_host_references_restricted_param_passes(self):
        """Host references a param with allowed_domains - should pass."""
        original = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        incoming = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        validate_host_references_domain_restricted_params(
            original, incoming, self._make_config("<domain>")
        )

    def test_host_references_unrestricted_param_fails(self):
        """Host switched to reference a param without allowed_domains - should fail."""
        original = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        incoming = [
            {"name": "domain", "allowed_domains": ["api.stripe.com"]},
            {"name": "my_host"},
        ]
        with pytest.raises(ValueError, match="does not have allowed_domains defined"):
            validate_host_references_domain_restricted_params(
                original, incoming, self._make_config("<my_host>")
            )

    def test_no_original_restrictions_passes(self):
        """If original config had no domain restrictions, anything goes."""
        original = [{"name": "domain"}, {"name": "api_key"}]
        incoming = [{"name": "domain"}, {"name": "api_key"}]
        validate_host_references_domain_restricted_params(
            original, incoming, self._make_config("<domain>")
        )

    def test_host_with_empty_allowed_domains_passes(self):
        """Host references a param with empty allowed_domains (self-hosted) - should pass."""
        original = [{"name": "domain", "allowed_domains": []}]
        incoming = [{"name": "domain", "allowed_domains": []}]
        validate_host_references_domain_restricted_params(
            original, incoming, self._make_config("<domain>")
        )

    def test_swap_host_to_unrestricted_new_param_fails(self):
        """Attack scenario: add new param without restrictions and swap host to it."""
        original = [
            {"name": "domain", "allowed_domains": ["api.stripe.com"]},
            {"name": "api_key"},
        ]
        incoming = [
            {"name": "domain", "allowed_domains": ["api.stripe.com"]},
            {"name": "api_key"},
            {"name": "evil_host"},
        ]
        with pytest.raises(ValueError, match="does not have allowed_domains defined"):
            validate_host_references_domain_restricted_params(
                original, incoming, self._make_config("<evil_host>")
            )

    def test_nested_endpoint_client_config_host_validated(self):
        """Nested client_config.host in endpoints should also be validated."""
        original = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        incoming = [
            {"name": "domain", "allowed_domains": ["api.stripe.com"]},
            {"name": "sneaky_host"},
        ]
        config = self._make_config(
            "<domain>",
            endpoints=[
                {
                    "name": "prospects",
                    "requests": {
                        "read": {
                            "client_config": {"host": "<sneaky_host>"},
                        }
                    },
                }
            ],
        )
        with pytest.raises(ValueError, match="does not have allowed_domains defined"):
            validate_host_references_domain_restricted_params(
                original, incoming, config
            )

    def test_nested_test_request_client_config_host_validated(self):
        """Nested client_config.host in test_request should also be validated."""
        original = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        incoming = [
            {"name": "domain", "allowed_domains": ["api.stripe.com"]},
            {"name": "other_host"},
        ]
        config = self._make_config(
            "<domain>",
            test_request={"client_config": {"host": "<other_host>"}},
        )
        with pytest.raises(ValueError, match="does not have allowed_domains defined"):
            validate_host_references_domain_restricted_params(
                original, incoming, config
            )

    def test_nested_host_with_allowed_domains_passes(self):
        """Nested client_config.host referencing a restricted param should pass."""
        original = [
            {"name": "domain", "allowed_domains": ["api.stripe.com"]},
            {"name": "other_domain", "allowed_domains": ["pi.pardot.com"]},
        ]
        incoming = [
            {"name": "domain", "allowed_domains": ["api.stripe.com"]},
            {"name": "other_domain", "allowed_domains": ["pi.pardot.com"]},
        ]
        config = self._make_config(
            "<domain>",
            endpoints=[
                {
                    "name": "prospects",
                    "requests": {
                        "read": {
                            "client_config": {"host": "<other_domain>"},
                        }
                    },
                }
            ],
        )
        validate_host_references_domain_restricted_params(original, incoming, config)

    def test_unknown_placeholder_fails(self):
        """Placeholder not in connector_params should fail when domain restrictions exist."""
        original = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        incoming = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        with pytest.raises(ValueError, match="not a known connector param"):
            validate_host_references_domain_restricted_params(
                original, incoming, self._make_config("<unknown_param>")
            )

    def test_direct_host_value_fails(self):
        """Direct host value (no placeholder) should fail when domain restrictions exist."""
        original = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        incoming = [{"name": "domain", "allowed_domains": ["api.stripe.com"]}]
        with pytest.raises(ValueError, match="does not reference any connector param"):
            validate_host_references_domain_restricted_params(
                original, incoming, self._make_config("evil.example.com")
            )
