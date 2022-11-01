from typing import Optional

from pydantic import Extra

from fides.api.ops.schemas.base_class import BaseSchema


class GetRegistrationStatusResponse(BaseSchema):
    """
    Reflects the registration status of a Fides deployment.
    """

    opt_in: bool = False

    class Config:
        """Only allow the `opt_in` status of this registration to be returned."""

        extra = Extra.forbid


class Registration(GetRegistrationStatusResponse):
    """
    Describes a Fides registration.
    """

    analytics_id: str
    opt_in: bool
    user_email: Optional[str]
    user_organization: Optional[str]
