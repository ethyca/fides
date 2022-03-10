from typing import Dict, Any

from sqlalchemy import Column, String
from sqlalchemy.orm import Session, relationship

from fidesops.core.config import config
from fidesops.db.base_class import Base
from fidesops.util.cryptographic_util import generate_salt, hash_with_salt


class FidesopsUser(Base):
    """The DB ORM model for FidesopsUser"""

    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    salt = Column(String, nullable=False)

    client = relationship(
        "ClientDetail", backref="user", cascade="all, delete", uselist=False
    )

    @classmethod
    def create(cls, db: Session, data: Dict[str, Any]) -> "FidesopsUser":
        """Create a FidesopsUser by hashing the password with a generated salt
        and storing the hashed password and the salt"""
        salt = generate_salt()
        hashed_password = hash_with_salt(
            data["password"].encode(config.security.ENCODING),
            salt.encode(config.security.ENCODING),
        )

        user = super().create(
            db,
            data={
                "salt": salt,
                "hashed_password": hashed_password,
                "username": data["username"],
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
