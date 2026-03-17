from sqlalchemy import Column, String, Text
from sqlalchemy.ext.declarative import declared_attr

from fides.api.db.base_class import Base


class EncryptionKey(Base):
    """
    Stores encrypted Data Encryption Keys (DEKs) for envelope encryption.

    Each row holds a DEK encrypted (wrapped) by the current Key Encryption Key (KEK).
    """

    @declared_attr
    def __tablename__(self) -> str:
        return "encryption_keys"

    wrapped_dek = Column(Text, nullable=False)
    kek_id_hash = Column(String, nullable=False)
    provider = Column(String, nullable=False, server_default="local")
