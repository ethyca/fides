from typing import Any, List

from pydantic import BaseModel


class FidesSchema(BaseModel):
    """A base template for all other Fides Schemas to inherit from."""

    @classmethod
    def get_field_names(cls) -> List[str]:
        """Return a list of all field names specified on this schema."""
        return list(cls.schema().get("properties", {}).keys())

    class Config:
        """Allow ORM access on all schemas."""

        orm_mode = True


BaseSchema = FidesSchema


class NoValidationSchema(BaseModel):
    """A schema to be used for API documentation only, when validation is
    handled later in the request process, but we still want valid request
    schemas to show up in the docs.
    """

    @classmethod
    def validate(cls, value: Any) -> Any:
        """Returns value exactly as it was passed in, when validation is
        going to be handled later.
        """
        return value
