class ResourceNotFoundError(Exception):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} '{resource_id}' not found")


class ResourceAlreadyExistsError(Exception):
    """Raised when creating a resource that already exists."""


class ResourceInUseError(Exception):
    """Raised when deleting a resource that is still referenced."""
