import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import EmailStr, validator

from fides.api.cryptography.cryptographic_util import decode_password
from fides.api.schemas.base_class import FidesSchema
from fides.api.schemas.oauth import AccessToken


class PrivacyRequestReviewer(FidesSchema):
    """Data we can expose via the PrivacyRequest.reviewer relation"""

    id: str
    username: str


class UserCreate(FidesSchema):
    """Data required to create a FidesUser."""

    username: str
    password: Optional[str]
    email_address: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    disabled: bool = False

    @validator("username")
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Ensure username does not have spaces."""
        if " " in username:
            raise ValueError("Usernames cannot have spaces.")
        return username

    @validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Add some password requirements"""
        decoded_password = decode_password(password)

        if len(decoded_password) < 8:
            raise ValueError("Password must have at least eight characters.")
        if re.search("[0-9]", decoded_password) is None:
            raise ValueError("Password must have at least one number.")
        if re.search("[A-Z]", decoded_password) is None:
            raise ValueError("Password must have at least one capital letter.")
        if re.search("[a-z]", decoded_password) is None:
            raise ValueError("Password must have at least one lowercase letter.")
        if re.search(r"[\W_]", decoded_password) is None:
            raise ValueError("Password must have at least one symbol.")

        return decoded_password


class UserCreateResponse(FidesSchema):
    """Response after creating a FidesUser"""

    id: str


class UserLogin(FidesSchema):
    """Similar to UserCreate except we do not need the extra validation on
    username and password.
    """

    username: str
    password: str

    @validator("password")
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Convert b64 encoded password to normal string"""
        return decode_password(password)


class UserResponse(FidesSchema):
    """Response after requesting a User"""

    id: str
    username: str
    created_at: datetime
    email_address: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]
    disabled: Optional[bool] = False
    disabled_reason: Optional[str]


class UserLoginResponse(FidesSchema):
    """Similar to UserResponse except with an access token"""

    user_data: UserResponse
    token_data: AccessToken


class UserPasswordReset(FidesSchema):
    """Contains both old and new passwords when resetting a password"""

    old_password: str
    new_password: str


class UserForcePasswordReset(FidesSchema):
    """Only a new password, for the case where the user does not remember their password"""

    new_password: str


class UserUpdate(FidesSchema):
    """Data required to update a FidesUser"""

    email_address: Optional[EmailStr]
    first_name: Optional[str]
    last_name: Optional[str]


class DisabledReason(Enum):
    """Reasons for why a user is disabled"""

    pending_invite = "pending_invite"
