from typing import Any, Dict

from sqlalchemy import Column, String
from sqlalchemy.orm import Session

from fides.api.db.base_class import Base


class AuthenticationRequest(Base):
    """
    Stores a reference between the state associated with an OAuth2 authentication request and a connector
    """

    connection_key = Column(String, index=False, unique=True, nullable=False)
    state = Column(String, index=True, unique=True, nullable=False)
    referer = Column(String, index=False, unique=False, nullable=True)

    @classmethod
    def create_or_update(cls, db: Session, *, data: Dict[str, Any]) -> "AuthenticationRequest":  # type: ignore[override]
        """
        Look up authentication request by connection_key. If found, update this authentication request, otherwise
        create a new one.
        """
        authentication_request = AuthenticationRequest.filter(
            db=db,
            conditions=(AuthenticationRequest.connection_key == data["connection_key"]),
        ).first()

        if authentication_request:
            authentication_request.update(db=db, data=data)
        else:
            authentication_request = cls.create(db=db, data=data)

        return authentication_request
