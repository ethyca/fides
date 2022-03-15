import re

from pydantic import validator

from fidesops.schemas.base_class import BaseSchema


class UserCreate(BaseSchema):
    """Data required to create a FidesopsUser"""

    username: str
    password: str

    @validator("username")
    def validate_username(cls, username: str) -> str:
        """Ensure password does not have spaces"""
        if not username:
            raise ValueError("Must enter username.")
        if " " in username:
            raise ValueError("Usernames cannot have spaces.")
        return username

    @validator("password")
    def validate_password(cls, password: str) -> str:
        """Add some password requirements"""
        if len(password) < 8:
            raise ValueError("Password must have at least eight characters.")
        if re.search("[0-9]", password) is None:
            raise ValueError("Password must have at least one number.")
        if re.search("[A-Z]", password) is None:
            raise ValueError("Password must have at least one capital letter.")
        if re.search("[a-z]", password) is None:
            raise ValueError("Password must have at least one lowercase letter.")
        if re.search(r"[\W]", password) is None:
            raise ValueError("Password must have at least one symbol.")

        return password


class UserLogin(BaseSchema):
    """Similar to UserCreate except we do not need the extra validation on username and password"""

    username: str
    password: str


class UserCreateResponse(BaseSchema):
    """Response after creating a FidesopsUser"""

    id: str
