from fastapi import APIRouter

from fideslang import FidesModel, model_map


routers = []
for resource_type, resource_model in model_map.items():
    router = APIRouter(tags=[resource_type], prefix=f"/{resource_type}")

    @router.post("/", response_model=resource_model)
    async def create(resource: FidesModel):
        """Create a resource."""
        return resource

    @router.get("/{fides_key}", response_model=resource_model)
    async def get(fides_key: str):
        """Get a resource by its fides_key."""
        return {"data": {"resource_type": resource_type, "fides_key": fides_key}}

    @router.post("/{fides_key}", response_model=resource_model)
    async def update(fides_key: str):
        """Update a resource by its fides_key."""

    @router.delete("/{fides_key}")
    async def delete(fides_key: str):
        """Delete a resource by its fides_key."""

    routers += [router]
