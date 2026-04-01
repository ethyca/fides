from typing import Optional

from sqlalchemy import Column, String, Text, select
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session

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

    @classmethod
    def get_by_provider(
        cls, session: Session, provider: str
    ) -> Optional["EncryptionKey"]:
        """Return the most recent encryption key row for the given provider."""
        stmt = (
            select(cls)
            .where(cls.provider == provider)
            .order_by(cls.created_at.desc())
            .limit(1)
        )
        return session.scalars(stmt).first()
