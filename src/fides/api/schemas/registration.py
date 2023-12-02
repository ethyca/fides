from typing import Optional

from pydantic import ConfigDict, EmailStr

from fides.api.schemas.base_class import FidesSchema


class GetRegistrationStatusResponse(FidesSchema):
    """
    Reflects the registration status of a Fides deployment.
    """

    opt_in: bool = False
    model_config = ConfigDict(extra="forbid")


class Registration(GetRegistrationStatusResponse):
    """
    Describes a Fides registration.
    """

    analytics_id: str
    opt_in: bool
    user_email: Optional[EmailStr]
    user_organization: Optional[str]
