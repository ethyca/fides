from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, Type

from sqlalchemy import (
    ARRAY,
    Column,
    ForeignKey,
    Index,
    String,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from fides.api.db.base_class import Base
from fides.api.db.util import EnumColumn
from fides.api.models.sql_models import System  # type: ignore[attr-defined]


class ConsentStatus(str, Enum):
    """
    Consent status of the asset
    """

    with_consent = "with_consent"
    without_consent = "without_consent"
    exempt = "exempt"
    unknown = "unknown"


class Asset(Base):
    """
    Web assets associated with a system
    """

    # Common attributes
    name = Column(String, index=True, nullable=False)
    asset_type = Column(String, index=True, nullable=False)
    domain = Column(String, index=True)
    parent = Column(ARRAY(String), server_default="{}", nullable=False)
    parent_domain = Column(String)
    locations = Column(ARRAY(String), server_default="{}", nullable=False)
    consent_status = Column(
        EnumColumn(ConsentStatus, native_enum=True),
        default=ConsentStatus.unknown,
        server_default="unknown",
        nullable=False,
    )
    data_uses = Column(ARRAY(String), server_default="{}", nullable=False)
    description = Column(String, nullable=True)
    page = Column(ARRAY(String), server_default="{}", nullable=False)

    # generic object to store additional attributes, specific to asset type
    meta = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        server_default="{}",
        default=dict,
    )

    # Browser request-specific attributes
    base_url = Column(String)

    system_id = Column(
        String, ForeignKey(System.id_field_path, ondelete="CASCADE"), index=True
    )  # If system is deleted, remove the associated assets.

    system = relationship(
        System,
        back_populates="assets",
        cascade="all,delete",
        uselist=False,
        lazy="selectin",
    )

    # we need to use an md5 of the base_url to avoid constraint/index length issues
    # and we need to use a unique index, rather than constraint, since postgresql constraints
    # do not support expressions, only direct column references
    __table_args__ = (
        Index(
            "ix_asset_name_asset_type_domain_base_url_system_id",
            name,
            asset_type,
            domain,
            func.coalesce(func.md5(base_url), "NULL"),
            system_id,
            unique=True,
        ),
    )

    @classmethod
    async def upsert_async(
        cls: Type[Asset],
        async_session: AsyncSession,
        *,
        data: Dict[str, Any],
    ) -> Asset:
        """
        Creates a new Asset record if it does not exist, otherwise updates the existing Asset record
        with the attribute values provided in the `data` dict.

        Assets are looked up by the provided attributes that make up their uniqueness criteria:
        - name
        - asset_type
        - domain
        - base_url (if applicable)
        - system_id

        If you provide the ID of an existing asset it will be updated with any provided data
        """
        if "id" not in data and (
            "name" not in data
            or "asset_type" not in data
            or "domain" not in data
            or "system_id" not in data
        ):
            raise ValueError(
                "name, asset_type, domain, and system_id are required fields on assets"
            )

        record_id: str

        if "id" in data:
            result = await async_session.execute(
                select(cls).where(cls.id == data["id"])  # type: ignore[arg-type]
            )
            existing_record = result.scalars().first()
            if existing_record:
                await async_session.execute(
                    update(cls).where(cls.id == existing_record.id).values(data)  # type: ignore[arg-type]
                )
                record_id = existing_record.id
            else:
                raise ValueError(f"Asset with id {data['id']} does not exist")
        else:
            result = await async_session.execute(
                select(cls).where(  # type: ignore[arg-type, call-arg]
                    cls.name == data["name"],
                    cls.asset_type == data["asset_type"],
                    cls.domain == data["domain"],
                    cls.base_url == data.get("base_url"),
                    cls.system_id == data["system_id"],
                )
            )

            existing_record = result.scalars().first()
            if existing_record:
                await async_session.execute(
                    update(cls).where(cls.id == existing_record.id).values(data)  # type: ignore[arg-type]
                )
                record_id = existing_record.id
            else:
                result = await async_session.execute(insert(cls).values(data))  # type: ignore[arg-type]
                record_id = result.inserted_primary_key.id

        result = await async_session.execute(select(cls).where(cls.id == record_id))  # type: ignore[arg-type]
        return result.scalars().first()

    @classmethod
    async def get_by_system_async(
        cls: Type[Asset],
        async_session: AsyncSession,
        system_id: Optional[str] = None,
        system_fides_key: Optional[str] = None,
    ) -> list[Asset]:
        """
        Retrieves all assets associated with a given system,
        using the provided system `id` or `fides_key`, whichever is provided
        """
        if system_id:
            query = select(cls).where(cls.system_id == system_id)  # type: ignore[arg-type]
        else:
            if not system_fides_key:
                raise ValueError(
                    "Either system_id or system_fides_key must be provided"
                )
            query = (
                select(cls)  # type: ignore[arg-type]
                .join(System, System.id == cls.system_id)  # type: ignore[attr-defined]
                .where(System.fides_key == system_fides_key)
            )

        result = await async_session.execute(query)
        return result.scalars().all()
