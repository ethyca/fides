from fides.api.ops.schemas.base_class import FidesSchema


class ClientCreatedResponse(FidesSchema):
    """Response schema for client creation"""

    client_id: str
    client_secret: str
