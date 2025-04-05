import re
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import ConfigDict, EmailStr, field_validator

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
    password: Optional[str] = None
    email_address: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: bool = False

    model_config = ConfigDict(extra="ignore")

    @field_validator("username")
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Ensure username does not have spaces."""
        if " " in username:
            raise ValueError("Usernames cannot have spaces.")
        return username

    @field_validator("password")
    @classmethod
    def validate_password_field(cls, password: str) -> str:
        """Add some password requirements"""
        decoded_password = decode_password(password)
        return UserCreate.validate_password(decoded_password)

    @staticmethod
    def validate_password(password: str) -> str:
        """
        Validate password requirements.
            Raises:
                ValueError: If password does not meet requirements
            Returns:
                str: password
        """
        if len(password) < 8:
            raise ValueError("Password must have at least eight characters.")
        if re.search(r"[\d]", password) is None:
            raise ValueError("Password must have at least one number.")
        if re.search("[A-Z]", password) is None:
            raise ValueError("Password must have at least one capital letter.")
        if re.search("[a-z]", password) is None:
            raise ValueError("Password must have at least one lowercase letter.")
        if re.search(r"[\W_]", password) is None:
            raise ValueError("Password must have at least one symbol.")

        return password


class UserCreateResponse(FidesSchema):
    """Response after creating a FidesUser"""

    id: str


class UserLogin(FidesSchema):
    """Similar to UserCreate except we do not need the extra validation on
    username and password.
    """

    username: str
    password: str

    @field_validator("password")
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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    disabled: Optional[bool] = False
    disabled_reason: Optional[str] = None


class UserLoginResponse(FidesSchema):
    """Similar to UserResponse except with an access token"""

    user_data: UserResponse
    token_data: AccessToken


class UserPasswordReset(FidesSchema):
    """Contains both old and new passwords when resetting a password"""

    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, password: str) -> str:
        """Add some password requirements"""
        decoded_password = decode_password(password)
        return UserCreate.validate_password(decoded_password)


class UserForcePasswordReset(FidesSchema):
    """Only a new password, for the case where the user does not remember their password"""

    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, password: str) -> str:
        """Add some password requirements"""
        decoded_password = decode_password(password)
        return UserCreate.validate_password(decoded_password)


class UserUpdate(FidesSchema):
    """Data required to update a FidesUser"""

    email_address: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class DisabledReason(Enum):
    """Reasons for why a user is disabled"""

    pending_invite = "pending_invite"
