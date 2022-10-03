from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Set, Union

from pydantic import BaseModel, Extra, root_validator, validator

from fidesops.ops.graph.config import (
    Collection,
    CollectionAddress,
    Dataset,
    FieldAddress,
    ScalarField,
)
from fidesops.ops.schemas.base_class import BaseSchema
from fidesops.ops.schemas.dataset import FidesCollectionKey, FidesopsDatasetReference
from fidesops.ops.schemas.saas.shared_schemas import HTTPMethod
from fidesops.ops.schemas.shared_schemas import FidesOpsKey


class ParamValue(BaseModel):
    """
    A named variable which can be sourced from identities, dataset references, or connector params. These values
    are used to replace the placeholders in the path, header, query, and body param values.
    """

    name: str
    identity: Optional[str]
    references: Optional[List[FidesopsDatasetReference]]
    connector_param: Optional[str]
    unpack: Optional[bool] = False

    @validator("references")
    def check_reference_direction(
        cls, references: Optional[List[FidesopsDatasetReference]]
    ) -> Optional[List[FidesopsDatasetReference]]:
        """Validates the request_param only contains inbound references"""
        for reference in references or {}:
            if reference.direction == "to":
                raise ValueError(
                    "References can only have a direction of 'from', found 'to'"
                )
        return references

    @root_validator
    def check_exactly_one_value_field(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        value_fields = [
            bool(values.get("identity")),
            bool(values.get("references")),
            bool(values.get("connector_param")),
        ]
        if sum(value_fields) != 1:
            raise ValueError(
                "Must have exactly one of 'identity', 'references', or 'connector_param'"
            )
        return values


class Strategy(BaseModel):
    """General shape for swappable strategies (ex: auth, processors, pagination, etc.)"""

    strategy: str
    configuration: Dict[str, Any]


class ClientConfig(BaseModel):
    """Definition for an authenticated base HTTP client"""

    protocol: str
    host: str
    authentication: Optional[Strategy]


class Header(BaseModel):
    name: str
    value: str


class QueryParam(BaseModel):
    name: str
    value: Union[int, str]


class SaaSRequest(BaseModel):
    """
    A single request with static or dynamic path, headers, query, and body params.
    Also specifies the names and sources for the param values needed to build the request.

    Includes optional strategies for postprocessing and pagination.
    """

    request_override: Optional[str]
    path: Optional[str]
    method: Optional[HTTPMethod]
    headers: Optional[List[Header]] = []
    query_params: Optional[List[QueryParam]] = []
    body: Optional[str]
    param_values: Optional[List[ParamValue]]
    client_config: Optional[ClientConfig]
    data_path: Optional[str]
    postprocessors: Optional[List[Strategy]]
    pagination: Optional[Strategy]
    grouped_inputs: Optional[List[str]] = []
    ignore_errors: Optional[bool] = False

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        orm_mode = True
        use_enum_values = True
        extra = Extra.forbid

    @root_validator(pre=True)
    def validate_request_for_pagination(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calls the appropriate validation logic for the request based on
        the specified pagination strategy. Passes in the raw value dict
        before any field validation.
        """

        # delay import to avoid cyclic-dependency error - We still ignore the pylint error
        from fidesops.ops.service.pagination.pagination_strategy import (  # pylint: disable=R0401
            PaginationStrategy,
        )

        pagination = values.get("pagination")
        if pagination is not None:
            pagination_strategy = PaginationStrategy.get_strategy(
                pagination.get("strategy"), pagination.get("configuration")
            )
            pagination_strategy.validate_request(values)
        return values

    @root_validator
    def validate_grouped_inputs(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that grouped_inputs must reference fields from the same collection"""
        grouped_inputs = set(values.get("grouped_inputs", []))

        if grouped_inputs:
            param_values = values.get("param_values", [])
            names = {param.name for param in param_values}

            if not grouped_inputs.issubset(names):
                raise ValueError(
                    "Grouped input fields must also be declared as param_values."
                )

            referenced_collections: List[str] = []
            for param in param_values:
                if param.name in grouped_inputs:
                    if not param.references and not param.identity:
                        raise ValueError(
                            "Grouped input fields must either be reference fields or identity fields."
                        )
                    if param.references:
                        collect = param.references[0].field.split(".")[0]
                        referenced_collections.append(collect)

            if len(set(referenced_collections)) != 1:
                raise ValueError(
                    "Grouped input fields must all reference the same collection."
                )

        return values

    @root_validator
    def validate_override(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that configs related to request overrides are set properly"""
        if not values.get("request_override"):
            if not values.get("path"):
                raise ValueError(
                    "A request must specify a path if no request_override is provided"
                )
            if not values.get("method"):
                raise ValueError(
                    "A request must specify a method if no request_override is provided"
                )

        else:  # if a request override is specified, many fields are NOT allowed
            invalid = [
                k
                for k in values.keys()
                if values.get(k)
                and k not in ("request_override", "param_values", "grouped_inputs")
            ]
            if invalid:
                invalid_joined = ", ".join(invalid)
                raise ValueError(
                    f"Invalid properties [{invalid_joined}] on a request with request_override specified"
                )

        return values


class Endpoint(BaseModel):
    """A collection of read/update/delete requests which corresponds to a FidesopsDataset collection (by name)"""

    name: str
    requests: Dict[Literal["read", "update", "delete"], SaaSRequest]
    after: List[FidesCollectionKey] = []


class ConnectorParam(BaseModel):
    """Used to define the required parameters for the connector (user and constants)"""

    name: str
    options: Optional[List[str]]  # list of possible values for the connector param
    default_value: Optional[Union[str, List[str]]]
    multiselect: Optional[bool] = False
    description: Optional[str]

    @root_validator
    def validate_connector_param(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the default_value is one of the values specified in the options list"""

        name = values.get("name")
        options: Optional[List[str]] = values.get("options")
        default_value: Optional[Union[str, List[str]]] = values.get("default_value")
        multiselect: Optional[bool] = values.get("multiselect")

        if options:
            if isinstance(default_value, str) and default_value not in options:
                raise ValueError(
                    f"'{default_value}' is not a valid option, default_value must be a value from [{', '.join(options)}]"
                )
            if isinstance(default_value, list):
                if not multiselect:
                    raise ValueError(
                        f"The default_value for the {name} connector_param must be a single value when multiselect is not enabled, not a list"
                    )

                invalid_options = [
                    value for value in default_value if value not in options
                ]
                if invalid_options:
                    raise ValueError(
                        f"[{', '.join(invalid_options)}] are not valid options, default_value must be a list of values from [{', '.join(options)}]"
                    )

        if multiselect and not options:
            raise ValueError(
                f"The 'multiselect' field in the {name} connector_param must be accompanied by an 'options' field containing a list of values."
            )

        return values


class SaaSType(Enum):
    """
    Enum to store saas connection type in Fidesops
    """

    adobe_campaign = "adobe_campaign"
    auth0 = "auth0"
    shopify = "shopify"
    mailchimp = "mailchimp"
    hubspot = "hubspot"
    outreach = "outreach"
    salesforce = "salesforce"
    segment = "segment"
    sentry = "sentry"
    stripe = "stripe"
    zendesk = "zendesk"
    custom = "custom"
    sendgrid = "sendgrid"
    datadog = "datadog"
    rollbar = "rollbar"
    braze = "braze"
    firebase_auth = "firebase_auth"


class SaaSConfigBase(BaseModel):
    """
    Used to store base info for a saas config
    """

    fides_key: FidesOpsKey
    name: str
    type: SaaSType

    @property
    def fides_key_prop(self) -> FidesOpsKey:
        return self.fides_key

    @property
    def name_prop(self) -> str:
        return self.name

    @validator("type", pre=True)
    def lowercase_saas_type(cls, value: str) -> str:
        """Enforce lowercase on saas type."""
        return value.lower()

    class Config:
        """Populate models with the raw value of enum fields, rather than the enum itself"""

        use_enum_values = True


class SaaSConfig(SaaSConfigBase):
    """
    Used to store endpoint and param configurations for a SaaS connector.
    This is done to separate the details of how to make the API calls
    from the data provided by a given API collection.

    The required fields for the config are converted into a Dataset which is
    merged with the standard Fidesops Dataset to provide a complete set of dependencies
    for the graph traversal.
    """

    description: str
    version: str
    connector_params: List[ConnectorParam]
    client_config: ClientConfig
    endpoints: List[Endpoint]
    test_request: SaaSRequest
    data_protection_request: Optional[SaaSRequest] = None  # GDPR Delete

    @property
    def top_level_endpoint_dict(self) -> Dict[str, Endpoint]:
        """Returns a map of endpoint names mapped to Endpoints"""
        return {endpoint.name: endpoint for endpoint in self.endpoints}

    def get_graph(self) -> Dataset:
        """Converts endpoints to a Dataset with collections and field references"""
        collections = []
        for endpoint in self.endpoints:
            fields = []
            for param in endpoint.requests["read"].param_values or []:
                if param.references:
                    references = []
                    for reference in param.references:
                        first, *rest = reference.field.split(".")
                        references.append(
                            (
                                FieldAddress(reference.dataset, first, *rest),
                                reference.direction,
                            )
                        )
                    fields.append(ScalarField(name=param.name, references=references))
                if param.identity:
                    fields.append(ScalarField(name=param.name, identity=param.identity))
            if fields:
                grouped_inputs: Optional[Set[str]] = set()
                if endpoint.requests.get("read"):
                    grouped_inputs = set(endpoint.requests["read"].grouped_inputs or [])
                collections.append(
                    Collection(
                        name=endpoint.name,
                        fields=fields,
                        grouped_inputs=grouped_inputs,
                        after={
                            CollectionAddress(*s.split(".")) for s in endpoint.after
                        },
                    )
                )

        return Dataset(
            name=super().name_prop,
            collections=collections,
            connection_key=super().fides_key_prop,
        )


class SaaSConfigValidationDetails(BaseSchema):
    """
    Message with any validation issues with the SaaS config
    """

    msg: Optional[str]


class ValidateSaaSConfigResponse(BaseSchema):
    """
    Response model for validating a SaaS config, which includes both the SaaS config
    itself (if valid) plus a details object describing any validation errors.
    """

    saas_config: SaaSConfig
    validation_details: SaaSConfigValidationDetails
