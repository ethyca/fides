from datetime import datetime
from typing import Dict, Any, Tuple

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Session, relationship

from fidesops.core.config import config
from fidesops.db.base_class import Base
from fidesops.util.cryptographic_util import generate_salt, hash_with_salt


class FidesopsUser(Base):
    """The DB ORM model for FidesopsUser"""

    username = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_at = Column(DateTime(timezone=True), nullable=True)

    client = relationship(
        "ClientDetail", backref="user", cascade="all, delete", uselist=False
    )

    @classmethod
    def hash_password(cls, password: str) -> Tuple[str, str]:
        """Utility function to hash a user's password with a generated salt"""
        salt = generate_salt()
        hashed_password = hash_with_salt(
            password.encode(config.security.ENCODING),
            salt.encode(config.security.ENCODING),
        )
        return hashed_password, salt

    @classmethod
    def create(cls, db: Session, data: Dict[str, Any]) -> "FidesopsUser":
        """Create a FidesopsUser by hashing the password with a generated salt
        and storing the hashed password and the salt"""
        hashed_password, salt = FidesopsUser.hash_password(data["password"])

        user = super().create(
            db,
            data={
                "salt": salt,
                "hashed_password": hashed_password,
                "username": data["username"],
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
            },
        )

        return user

    def credentials_valid(self, password: str) -> bool:
        """Verifies that the provided password is correct"""
        provided_password_hash = hash_with_salt(
            password.encode(config.security.ENCODING),
            self.salt.encode(config.security.ENCODING),
        )

        return provided_password_hash == self.hashed_password

    def update_password(self, db: Session, new_password: str) -> None:
        """Updates the user's password to the specified value.
        No validations are performed on the old/existing password within this function."""

        hashed_password, salt = FidesopsUser.hash_password(new_password)
        self.hashed_password = hashed_password
        self.salt = salt
        self.password_reset_at = datetime.utcnow()
        self.save(db)
