from fideslang.validation import AnyHttpUrlString
from pydantic import BaseModel, Field

from fides.api.schemas.base_class import NoValidationSchema


class WebsiteSchema(BaseModel):
    """Schema to validate the secrets needed for a generic website connector"""

    url: AnyHttpUrlString = Field(
        title="URL",
    )


class WebsiteDocsScehma(WebsiteSchema, NoValidationSchema):
    """Website Secrets Schema for API Docs"""
