import pytest
from fideslang.models import FidesDatasetReference
from pydantic import ValidationError

from fides.api.schemas.saas.saas_config import ParamValue, ReadSaaSRequest, SaaSRequest
from fides.api.schemas.saas.shared_schemas import HTTPMethod


class TestSaaSRequestSchema:
    def test_valid_saas_request(self):
        SaaSRequest(
            path="/api/v1/users",
            method=HTTPMethod.GET,
            headers=[{"name": "Authorization", "value": "Bearer token"}],
            query_params=[{"name": "limit", "value": "10"}],
            param_values=[ParamValue(name="email", identity="email")],
        )

    def test_missing_path(self):
        with pytest.raises(ValidationError) as exc:
            SaaSRequest()
        assert (
            "A request must specify a path if no request_override is provided"
            in str(exc.value)
        )

    def test_missing_method(self):
        with pytest.raises(ValidationError) as exc:
            SaaSRequest(path="/api/v1/users")
        assert (
            "A request must specify a method if no request_override is provided"
            in str(exc.value)
        )

    def test_request_override(self):
        request = SaaSRequest(request_override="read_request_override")
        assert request.request_override == "read_request_override"

    def test_invalid_fields_with_request_override(self):
        with pytest.raises(ValidationError) as exc:
            SaaSRequest(
                request_override="read_request_override",
                path="/api/v1/users",
                method=HTTPMethod.GET,
            )
        assert (
            "Invalid properties [path, method] on a request with request_override specified"
            in str(exc.value)
        )

    def test_valid_grouped_inputs(self):
        request = SaaSRequest(
            path="/api/v1/users",
            method=HTTPMethod.GET,
            param_values=[
                ParamValue(
                    name="user_id",
                    references=[
                        FidesDatasetReference(
                            dataset="dataset_key", field="users.id", direction="from"
                        )
                    ],
                ),
                ParamValue(
                    name="email",
                    references=[
                        FidesDatasetReference(
                            dataset="dataset_key", field="users.email", direction="from"
                        )
                    ],
                ),
            ],
            grouped_inputs=["user_id", "email"],
        )
        assert request.grouped_inputs == ["user_id", "email"]

    def test_invalid_grouped_inputs(self):
        with pytest.raises(ValidationError) as exc:
            SaaSRequest(
                path="/api/v1/users",
                method=HTTPMethod.GET,
                param_values=[
                    ParamValue(
                        name="user_id",
                        references=[
                            FidesDatasetReference(
                                dataset="dataset_key",
                                field="users.id",
                                direction="from",
                            )
                        ],
                    ),
                    ParamValue(
                        name="email",
                        references=[
                            FidesDatasetReference(
                                dataset="dataset_key",
                                field="customers.email",
                                direction="from",
                            )
                        ],
                    ),
                ],
                grouped_inputs=["user_id", "email"],
            )
        assert "Grouped input fields must all reference the same collection" in str(
            exc.value
        )

    def test_grouped_inputs_not_in_param_values(self):
        with pytest.raises(ValidationError) as exc:
            SaaSRequest(
                path="/api/v1/users",
                method=HTTPMethod.GET,
                param_values=[
                    ParamValue(
                        name="user_id",
                        references=[
                            FidesDatasetReference(
                                dataset="dataset_key",
                                field="users.id",
                                direction="from",
                            )
                        ],
                    )
                ],
                grouped_inputs=["user_id", "email"],
            )
        assert "Grouped input fields must also be declared as param_values" in str(
            exc.value
        )


class TestReadSaaSRequestSchema:
    def test_valid_read_saas_request(self):
        request = ReadSaaSRequest(
            path="/api/v1/users",
            method=HTTPMethod.GET,
            output='{"user_id": "<user_id>"}',
        )
        assert request.path == "/api/v1/users"
        assert request.method == HTTPMethod.GET.value
        assert request.output == '{"user_id": "<user_id>"}'

    def test_missing_path_and_output(self):
        with pytest.raises(ValidationError) as exc:
            ReadSaaSRequest(method=HTTPMethod.GET)
        assert (
            "A read request must specify either a path or an output if no request_override is provided"
            in str(exc.value)
        )

    def test_missing_method_with_path(self):
        with pytest.raises(ValidationError) as exc:
            ReadSaaSRequest(path="/api/v1/users")
        assert (
            "A read request must specify a method if a path is provided and no request_override is specified"
            in str(exc.value)
        )

    def test_valid_read_request_with_output_only(self):
        request = ReadSaaSRequest(output='{"user_id": "<user_id>"}')
        assert request.output == '{"user_id": "<user_id>"}'

    def test_read_request_override_with_output(self):
        with pytest.raises(ValidationError) as exc:
            ReadSaaSRequest(
                request_override="read_request_override",
                output='{"user_id": "<user_id>"}',
            )
        assert (
            "Invalid properties [output] on a read request with request_override specified"
            in str(exc.value)
        )

    def test_invalid_fields_with_read_request_override(self):
        with pytest.raises(ValidationError) as exc:
            ReadSaaSRequest(
                request_override="read_request_override",
                path="/api/v1/users",
                method=HTTPMethod.GET,
                output='{"user_id": "<user_id>"}',
            )
        assert (
            "Invalid properties [path, method, output] on a read request with request_override specified"
            in str(exc.value)
        )
