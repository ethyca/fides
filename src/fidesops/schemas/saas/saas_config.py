from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, validator
from fidesops.schemas.base_class import BaseSchema
from fidesops.schemas.dataset import FidesopsDatasetReference
from fidesops.graph.config import Collection, Dataset, FieldAddress, ScalarField
from fidesops.schemas.shared_schemas import FidesOpsKey


class ConnectorParams(BaseModel):
    """
    Required information for the given SaaS connector.
    """

    name: str


class RequestParam(BaseModel):
    """
    A request parameter which includes the type (query or path) along with a default value or
    a reference to an identity value or a value in another dataset.
    """

    name: str
    type: Literal[
        "query", "path"
    ]  # used to determine location in the generated request
    default_value: Optional[Any]
    identity: Optional[str]
    data_type: Optional[str]
    references: Optional[List[FidesopsDatasetReference]]

    @validator("references")
    def check_references_or_identity(
        cls,
        references: Optional[List[FidesopsDatasetReference]],
        values: Dict[str, str],
    ) -> Optional[List[FidesopsDatasetReference]]:
        """Validates that each request_param only has an identity or references, not both"""
        if values["identity"] is not None and references is not None:
            raise ValueError(
                "Can only have one of 'reference' or 'identity' per request_param, not both"
            )
        return references

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


class Strategy(BaseModel):
    """General shape for swappable strategies (ex: auth, pagination, postprocessing, etc.)"""

    strategy: str
    configuration: Dict[str, Any]


class SaaSRequest(BaseModel):
    """
    A single request with a static or dynamic path, and the request params needed to build the request.
    Also includes optional strategies for pre/postprocessing and pagination.
    """

    path: str
    request_params: Optional[List[RequestParam]]
    data_path: Optional[str]  # defaults to collection name if not specified
    preprocessor: Optional[Strategy]
    postprocessor: Optional[List[Strategy]]
    pagination: Optional[Strategy]


class Endpoint(BaseModel):
    """An collection of read/update/delete requests which corresponds to a FidesopsDataset collection (by name)"""

    name: str
    requests: Dict[Literal["read", "update", "delete"], SaaSRequest]


class ConnectorParam(BaseModel):
    """Used to define the required parameters for the connector (user-provided and constants)"""

    name: str
    default_value: Optional[Any]


class ConnectorParamRef(BaseModel):
    """A reference to a value in the connector params (by name)"""

    connector_param: str


class ClientConfig(BaseModel):
    """Definition for an authenticated base HTTP client"""

    protocol: str
    host: Union[
        str, ConnectorParamRef
    ]  # can be defined inline or be a connector_param reference
    authentication: Strategy


class SaaSConfig(BaseModel):
    """
    Used to store endpoint and param configurations for a SaaS connector.
    This is done to separate the details of how to make the API calls
    from the data provided by a given API collection.

    The required fields for the config are converted into a Dataset which is
    merged with the standard Fidesops Dataset to provide a complete set of dependencies
    for the graph traversal
    """

    fides_key: FidesOpsKey
    name: str
    description: str
    version: str
    connector_params: List[ConnectorParam]
    client_config: ClientConfig
    endpoints: List[Endpoint]
    test_request: SaaSRequest

    @property
    def top_level_endpoint_dict(self) -> Dict[str, Endpoint]:
        """Returns a map of endpoint names mapped to Endpoints"""
        return {endpoint.name: endpoint for endpoint in self.endpoints}

    def get_graph(self) -> Dataset:
        """Converts endpoints to a Dataset with collections and field references"""
        collections = []
        for endpoint in self.endpoints:
            fields = []
            for param in endpoint.requests["read"].request_params or []:
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
                collections.append(Collection(name=endpoint.name, fields=fields))

        return Dataset(
            name=self.name,
            collections=collections,
            connection_key=self.fides_key,
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
