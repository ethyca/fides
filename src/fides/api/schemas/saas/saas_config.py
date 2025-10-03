from typing import Any, Dict, List, Optional, Set, Union

from fideslang.models import FidesCollectionKey, FidesDatasetReference
from fideslang.validation import FidesKey
from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField
from pydantic import field_validator, model_validator

from fides.api.common_exceptions import ValidationError
from fides.api.graph.config import (
    Collection,
    CollectionAddress,
    Field,
    FieldAddress,
    GraphDataset,
    ScalarField,
)
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.limiter.rate_limit_config import RateLimitConfig
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.display_info import SaaSDisplayInfo
from fides.api.schemas.saas.shared_schemas import HTTPMethod
from fides.api.service.saas_request.saas_request_override_factory import (
    SaaSRequestOverrideFactory,
    SaaSRequestType,
)


class ParamValue(BaseModel):
    """
    A named variable which can be sourced from identities, dataset references, or connector params. These values
    are used to replace the placeholders in the path, header, query, and body param values.
    """

    name: str
    identity: Optional[str] = None
    references: Optional[List[Union[FidesDatasetReference, str]]] = None
    connector_param: Optional[str] = None
    unpack: Optional[bool] = False

    @field_validator("references")
    @classmethod
    def check_reference_direction(
        cls, references: Optional[List[Union[FidesDatasetReference, str]]]
    ) -> Optional[List[Union[FidesDatasetReference, str]]]:
        """Validates the request_param only contains inbound references"""
        for reference in references or {}:
            if isinstance(reference, FidesDatasetReference):
                if reference.direction == "to":
                    raise ValueError(
                        "References can only have a direction of 'from', found 'to'"
                    )
        return references

    @model_validator(mode="after")
    def check_exactly_one_value_field(self) -> "ParamValue":
        value_fields = [
            bool(self.identity),
            bool(self.references),
            bool(self.connector_param),
        ]
        if sum(value_fields) != 1:
            raise ValueError(
                "Must have exactly one of 'identity', 'references', or 'connector_param'"
            )
        return self


class Strategy(BaseModel):
    """General shape for swappable strategies (ex: auth, processors, pagination, etc.)"""

    strategy: str
    configuration: Optional[Dict[str, Any]] = None


class ClientConfig(BaseModel):
    """Definition for an authenticated base HTTP client"""

    protocol: str
    host: str
    authentication: Optional[Strategy] = None


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

    request_override: Optional[str] = None
    path: Optional[str] = None
    method: Optional[HTTPMethod] = None
    headers: Optional[List[Header]] = []
    query_params: Optional[List[QueryParam]] = []
    body: Optional[str] = None
    param_values: Optional[List[ParamValue]] = []
    client_config: Optional[ClientConfig] = None
    data_path: Optional[str] = None
    postprocessors: Optional[List[Strategy]] = None
    pagination: Optional[Strategy] = None
    grouped_inputs: Optional[List[str]] = []
    ignore_errors: Optional[Union[bool, List[int]]] = False
    rate_limit_config: Optional[RateLimitConfig] = None
    async_config: Optional[Strategy] = None
    skip_missing_param_values: Optional[bool] = (
        False  # Skip instead of raising an exception if placeholders can't be populated in body
    )
    correlation_id_path: Optional[str] = PydanticField(
        default=None,
        description="The path to the correlation ID in the response. For use with async polling.",
    )
    model_config = ConfigDict(
        from_attributes=True, use_enum_values=True, extra="forbid"
    )

    @model_validator(mode="after")
    def validate_request_for_pagination(self) -> "SaaSRequest":
        """
        Calls the appropriate validation logic for the request based on
        the specified pagination strategy. Passes in the raw value dict
        before any field validation.
        """

        # delay import to avoid cyclic-dependency error - We still ignore the pylint error
        from fides.api.service.pagination.pagination_strategy import (  # pylint: disable=R0401
            PaginationStrategy,
        )

        pagination = self.pagination
        if pagination is not None:
            pagination_strategy = PaginationStrategy.get_strategy(
                pagination.strategy, pagination.configuration
            )
            pagination_strategy.validate_request(self.model_dump(mode="json"))
        return self

    @model_validator(mode="after")
    def validate_grouped_inputs(self) -> "SaaSRequest":
        """Validate that grouped_inputs must reference fields from the same collection"""
        grouped_inputs = set(self.grouped_inputs or [])

        if grouped_inputs:
            param_values = self.param_values or []
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
                        # reference may be a str, in which case it's an external reference.
                        # since external references are parameterized via secrets,
                        # they cannot be resolved and checked at this point in the validation.
                        # so here we only perform the check if the reference is a FidesDatasetReference
                        if isinstance(param.references[0], FidesDatasetReference):
                            collect = param.references[0].field.split(".")[0]
                            referenced_collections.append(collect)
                        else:
                            raise ValueError(
                                "Grouped inputs do not currently support external dataset references"
                            )

            if len(set(referenced_collections)) != 1:
                raise ValueError(
                    "Grouped input fields must all reference the same collection."
                )

        return self

    @model_validator(mode="after")
    def validate_request(self) -> "SaaSRequest":
        """Validate that configs related to request overrides are set properly"""
        if not self.request_override:
            if not self.path:
                raise ValueError(
                    "A request must specify a path if no request_override is provided"
                )
            if not self.method:
                raise ValueError(
                    "A request must specify a method if no request_override is provided"
                )

        else:  # if a request override is specified, many fields are NOT allowed
            invalid = [
                k
                for k in self.model_fields
                if getattr(self, k)
                and k not in ("request_override", "param_values", "grouped_inputs")
            ]
            if invalid:
                invalid_joined = ", ".join(invalid)
                raise ValueError(
                    f"Invalid properties [{invalid_joined}] on a request with request_override specified"
                )

        return self


class ReadSaaSRequest(SaaSRequest):
    """
    An extension of the base SaaSRequest that allows the inclusion of an output template
    that is used to format each collection result, and correlation_id_path for async polling.
    """

    output: Optional[str] = None

    @model_validator(mode="after")
    def validate_request(self) -> "ReadSaaSRequest":
        """Validate that configs related to read requests are set properly"""
        if not self.request_override:
            if not (self.path or self.output):
                raise ValueError(
                    "A read request must specify either a path or an output if no request_override is provided"
                )
            if self.path and not self.method:
                raise ValueError(
                    "A read request must specify a method if a path is provided and no request_override is specified"
                )

        if self.request_override:
            allowed_fields = {
                "request_override",
                "param_values",
                "grouped_inputs",
            }
            invalid = [
                k
                for k in self.model_fields
                if getattr(self, k) and k not in allowed_fields
            ]
            if invalid:
                invalid_joined = ", ".join(invalid)
                raise ValueError(
                    f"Invalid properties [{invalid_joined}] on a read request with request_override specified"
                )
        return self


class SaaSRequestMap(BaseModel):
    """A map of actions to SaaS requests"""

    read: Union[ReadSaaSRequest, List[ReadSaaSRequest]] = []
    update: Optional[SaaSRequest] = None
    delete: Optional[SaaSRequest] = None


class ConsentRequestMap(BaseModel):
    """A map of actions to Consent requests"""

    opt_in: Union[SaaSRequest, List[SaaSRequest]] = []
    opt_out: Union[SaaSRequest, List[SaaSRequest]] = []

    @field_validator("opt_in", "opt_out")
    @classmethod
    def validate_list_field(
        cls,
        field_value: Union[SaaSRequest, List[SaaSRequest]],
    ) -> List[SaaSRequest]:
        """Convert all opt_in/opt_out request formats to a list of requests.

        We allow either a single request or a list of requests to be defined, but this makes
        sure that everything is a list once that data has been read in.
        """
        if isinstance(field_value, SaaSRequest):
            return [field_value]
        return field_value


class Endpoint(BaseModel):
    """A collection of read/update/delete requests which corresponds to a FidesDataset collection (by name)"""

    name: str
    requests: SaaSRequestMap
    skip_processing: bool = False
    after: List[FidesCollectionKey] = []
    erase_after: List[FidesCollectionKey] = []

    @field_validator("requests")
    @classmethod
    def validate_grouped_inputs(
        cls,
        requests: SaaSRequestMap,
    ) -> SaaSRequestMap:
        """Validate that grouped_inputs are the same for every read request"""

        read_requests = requests.read
        if isinstance(read_requests, list) and len(read_requests) > 1:
            first, *rest = read_requests
            if not all(
                request.grouped_inputs == first.grouped_inputs for request in rest
            ):
                raise ValueError(
                    "The grouped_input values for every read request must be the same"
                )
        return requests


class ConnectorParam(BaseModel):
    """Used to define the required parameters for the connector (user and constants)"""

    name: str
    label: Optional[str] = None
    options: Optional[List[str]] = (
        None  # list of possible values for the connector param
    )
    # If you change the default_value type, update this in SaaSSchemaFactory.get_saas_schema
    default_value: Optional[Union[str, List[str], int, List[int]]] = None
    multiselect: Optional[bool] = False
    description: Optional[str] = None
    sensitive: Optional[bool] = False

    @model_validator(mode="before")
    @classmethod
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


class ExternalDatasetReference(BaseModel):
    name: str
    label: Optional[str] = None
    description: Optional[str] = None


class SaaSConfigBase(BaseModel):
    """
    Used to store base info for a SaaS config
    """

    fides_key: FidesKey
    name: str
    type: str

    @property
    def fides_key_prop(self) -> FidesKey:
        return self.fides_key

    @property
    def name_prop(self) -> str:
        return self.name

    @field_validator("type", mode="before")
    @classmethod
    def lowercase_saas_type(cls, value: str) -> str:
        """Enforce lowercase on saas type."""
        return value.lower()

    model_config = ConfigDict(use_enum_values=True)


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
    replaceable: bool = False
    connector_params: List[ConnectorParam]
    external_references: Optional[List[ExternalDatasetReference]] = None
    client_config: ClientConfig
    endpoints: List[Endpoint]
    test_request: SaaSRequest
    data_protection_request: Optional[SaaSRequest] = None  # GDPR Delete
    rate_limit_config: Optional[RateLimitConfig] = None
    consent_requests: Optional[ConsentRequestMap] = None
    user_guide: Optional[str] = None
    display_info: Optional[SaaSDisplayInfo] = None

    @property
    def top_level_endpoint_dict(self) -> Dict[str, Endpoint]:
        """Returns a map of endpoint names mapped to Endpoints"""
        return {endpoint.name: endpoint for endpoint in self.endpoints}

    def get_graph(self, secrets: Dict[str, Any]) -> GraphDataset:
        """Converts endpoints to a Dataset with collections and field references"""
        collections = []
        for endpoint in self.endpoints:
            fields: List[Field] = []

            read_requests: List[ReadSaaSRequest] = []
            if endpoint.requests.read:
                read_requests = (
                    endpoint.requests.read
                    if isinstance(endpoint.requests.read, list)
                    else [endpoint.requests.read]
                )

            delete_request = endpoint.requests.delete

            for read_request in read_requests:
                self._process_param_values(fields, read_request.param_values, secrets)

            if not read_requests and delete_request:
                # If the endpoint only specifies a delete request without a read,
                # then we must use the delete request's param_values instead.
                # One of the fields must automatically be flagged as a primary key
                # in order for the deletion to execute. See fides#1199
                self._process_param_values(fields, delete_request.param_values, secrets)
                if fields:
                    fields[0].primary_key = True

            if fields:
                grouped_inputs: Set[str] = set()
                if read_requests:
                    # the endpoint validator enforces that grouped inputs are the same
                    # for all read requests so we can just take the first one
                    grouped_inputs = set(read_requests[0].grouped_inputs or [])
                collections.append(
                    Collection(
                        name=endpoint.name,
                        fields=fields,
                        grouped_inputs=grouped_inputs,
                        skip_processing=endpoint.skip_processing,  # Sets this value for use when datasets are merged. If True, this will be later be removed.
                        after={
                            CollectionAddress(*s.split(".")) for s in endpoint.after
                        },
                        erase_after={
                            CollectionAddress(*s.split("."))
                            for s in endpoint.erase_after
                        },
                    )
                )

        return GraphDataset(
            name=super().name_prop,
            collections=collections,
            connection_key=super().fides_key_prop,
        )

    def _process_param_values(
        self,
        fields: List[Field],
        param_values: Optional[List[ParamValue]],
        secrets: Dict[str, Any],
    ) -> None:
        """
        Converts param values to dataset fields with identity and dataset references
        """
        for param in param_values or []:
            if param.references:
                references = []
                for reference in param.references:
                    resolved_reference = self.resolve_param_reference(
                        reference, secrets
                    )
                    first, *rest = resolved_reference.field.split(".")
                    references.append(
                        (
                            FieldAddress(resolved_reference.dataset, first, *rest),
                            (
                                # Convert back into a literal for Pydantic V2
                                resolved_reference.direction.value
                                if resolved_reference.direction
                                else resolved_reference.direction
                            ),
                        )
                    )
                fields.append(ScalarField(name=param.name, references=references))
            if param.identity:
                fields.append(ScalarField(name=param.name, identity=param.identity))

    @staticmethod
    def resolve_param_reference(
        reference: Union[str, FidesDatasetReference], secrets: Dict[str, Any]
    ) -> FidesDatasetReference:
        """
        If needed, resolves the given `reference` using the provided `secrets` `dict`.
        For ease of use, the given `reference` can either be a `str` or `FidesDatasetReference`,
        since a `ParamValue`'s `reference` may be of either type.

        If the `reference` is a `str`, then it's used as a key look up a value in the provided secrets dict,
        and a `FidesDatasetReference` is created and returned from the retrieved secrets object.

        If the `reference` is a `FidesDatasetReference`, then it's just returned as-is.
        """
        if isinstance(reference, str):
            if reference not in secrets.keys():
                raise ValidationError(
                    f"External dataset reference with provided name {reference} not found in connector's secrets."
                )
            reference = FidesDatasetReference.model_validate(secrets[reference])
        return reference

    @property
    def supported_actions(self) -> List[ActionType]:
        """Returns a list containing the privacy actions supported by the SaaS config."""

        supported_actions = []

        # check for access
        if any(
            requests.read
            for requests in [endpoint.requests for endpoint in self.endpoints]
        ):
            supported_actions.append(ActionType.access)

        # check for erasure
        if (
            any(
                request.update or request.delete
                for request in [endpoint.requests for endpoint in self.endpoints]
            )
            or self.data_protection_request
        ):
            supported_actions.append(ActionType.erasure)

        # consent is supported if the SaaSConfig has consent_requests defined
        # or if the SaaSConfig.type has an UPDATE_CONSENT function
        # registered in the SaaSRequestOverrideFactory
        if (
            self.consent_requests
            or self.type
            in SaaSRequestOverrideFactory.registry[
                SaaSRequestType.UPDATE_CONSENT
            ].keys()
        ):
            supported_actions.append(ActionType.consent)

        return supported_actions


class SaaSConfigValidationDetails(FidesSchema):
    """
    Message with any validation issues with the SaaS config
    """

    msg: Optional[str] = None


class ValidateSaaSConfigResponse(FidesSchema):
    """
    Response model for validating a SaaS config, which includes both the SaaS config
    itself (if valid) plus a details object describing any validation errors.
    """

    saas_config: SaaSConfig
    validation_details: SaaSConfigValidationDetails
