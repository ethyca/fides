from fidesops.schemas.base_class import FidesopsSchema


class ClientCreatedResponse(FidesopsSchema):
    """Response schema for client creation"""

    client_id: str
    client_secret: str
