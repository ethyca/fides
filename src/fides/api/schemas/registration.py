from typing import Optional

from pydantic import EmailStr, Extra

from fides.api.schemas.base_class import FidesSchema


class GetRegistrationStatusResponse(FidesSchema):
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
    user_email: Optional[EmailStr]
    user_organization: Optional[str]
