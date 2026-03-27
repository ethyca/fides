import enum

from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base
from fides.api.db.encryption_utils import encrypted_type
from fides.api.models.connectionconfig import ConnectionConfig

# pylint: disable=unused-import
from fides.api.models.sql_models import System  # type: ignore[attr-defined]


class OAuthGrantType(enum.Enum):
    authorization_code = "authorization_code"
    client_credentials = "client_credentials"
    password = "password"
    implicit = "implicit"


class OAuthConfig(Base):
    """
    Stores credentials to connect fidesops to anything that uses OAuth2 for authentication.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        """Overriding base class method to set the table name."""
        return "oauth_config"

    connection_config_id = Column(
        String, ForeignKey(ConnectionConfig.id_field_path), nullable=False
    )

    grant_type = Column(Enum(OAuthGrantType), nullable=False)
    token_url = Column(String, nullable=False)
    scope = Column(String, nullable=True)
    client_id = Column(String, nullable=False)
    client_secret = Column(
        encrypted_type(type_in=String()),
        nullable=False,
    )

    connection_config = relationship(
        "ConnectionConfig",
        back_populates="oauth_config",
    )
