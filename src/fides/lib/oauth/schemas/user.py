import re
from datetime import datetime
from typing import Optional

from pydantic import validator

from fides.lib.cryptography.cryptographic_util import decode_password
from fides.lib.oauth.schemas.oauth import AccessToken
from fides.lib.schemas.base_class import BaseSchema


class PrivacyRequestReviewer(BaseSchema):
    """Data we can expose via the PrivacyRequest.reviewer relation"""

    id: str
    username: str


class UserCreate(BaseSchema):
    """Data required to create a FidesUser."""

    username: str
    password: str
    first_name: Optional[str]
    last_name: Optional[str]

    @validator("username")
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Ensure password does not have spaces."""
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
        if re.search(r"[\W]", decoded_password) is None:
            raise ValueError("Password must have at least one symbol.")

        return decoded_password


class UserCreateResponse(BaseSchema):
    """Response after creating a FidesUser"""

    id: str


class UserLogin(BaseSchema):
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


class UserResponse(BaseSchema):
    """Response after requesting a User"""

    id: str
    username: str
    created_at: datetime
    first_name: Optional[str]
    last_name: Optional[str]


class UserLoginResponse(BaseSchema):
    """Similar to UserResponse except with an access token"""

    user_data: UserResponse
    token_data: AccessToken


class UserPasswordReset(BaseSchema):
    """Contains both old and new passwords when resetting a password"""

    old_password: str
    new_password: str


class UserUpdate(BaseSchema):
    """Data required to update a FidesopsUser"""

    first_name: Optional[str]
    last_name: Optional[str]
