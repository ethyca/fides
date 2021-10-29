from typing import List

from pydantic import BaseModel


class FidesopsSchema(BaseModel):
    """
    A base template for all other FidesOps Schemas to inherit from.
    """

    @classmethod
    def get_field_names(cls) -> List[str]:
        """Return a list of all field names specified on this schema"""
        return list(cls.schema().get("properties", {}).keys())

    class Config:
        """Allow ORM access on all schemas"""

        orm_mode = True


BaseSchema = FidesopsSchema
