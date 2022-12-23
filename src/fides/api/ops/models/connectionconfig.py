from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, Optional, Type

from sqlalchemy import Boolean, Column, DateTime, Enum, String, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session, relationship
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.ops.db.base_class import JSONTypeOverride
from fides.api.ops.schemas.saas.saas_config import SaaSConfig
from fides.core.config import get_config
from fides.lib.db.base import Base  # type: ignore[attr-defined]
from fides.lib.db.base_class import get_key_from_data
from fides.lib.exceptions import KeyOrNameAlreadyExists

CONFIG = get_config()


class ConnectionTestStatus(enum.Enum):
    """Enum for supplying statuses of validating credentials for a Connection Config to the user"""

    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class ConnectionType(enum.Enum):
    """
    Supported types to which we can connect fidesops.
    """

    postgres = "postgres"
    mongodb = "mongodb"
    mysql = "mysql"
    https = "https"
    saas = "saas"
    redshift = "redshift"
    snowflake = "snowflake"
    mssql = "mssql"
    mariadb = "mariadb"
    bigquery = "bigquery"
    manual = "manual"  # Run as part of the traversal
    email = "email"
    manual_webhook = "manual_webhook"  # Run before the traversal
    timescale = "timescale"
    fides = "fides"

    @property
    def human_readable(self) -> str:
        """Human-readable mapping for ConnectionTypes
        Add to this mapping if you add a new ConnectionType
        """
        readable_mapping: Dict[str, str] = {
            ConnectionType.postgres.value: "PostgreSQL",
            ConnectionType.mongodb.value: "MongoDB",
            ConnectionType.mysql.value: "MySQL",
            ConnectionType.https.value: "Policy Webhook",
            ConnectionType.saas.value: "SaaS",
            ConnectionType.redshift.value: "Amazon Redshift",
            ConnectionType.snowflake.value: "Snowflake",
            ConnectionType.mssql.value: "Microsoft SQL Server",
            ConnectionType.mariadb.value: "MariaDB",
            ConnectionType.bigquery.value: "BigQuery",
            ConnectionType.manual.value: "Manual Connector",
            ConnectionType.email.value: "Email Connector",
            ConnectionType.manual_webhook.value: "Manual Webhook",
            ConnectionType.timescale.value: "TimescaleDB",
            ConnectionType.fides.value: "Fides Connector",
        }
        try:
            return readable_mapping[self.value]
        except KeyError:
            raise NotImplementedError(
                "Add new ConnectionType to human_readable mapping"
            )


class AccessLevel(enum.Enum):
    """
    Perms given to the ConnectionConfig.  For example, with "read" permissions, fidesops promises
    to not modify the data on a connected application database in any way.

    "Write" perms mean we can update/delete items in the connected database.
    """

    read = "read"
    write = "write"


class ConnectionConfig(Base):
    """
    Stores credentials to connect fidesops to an engineer's application databases.
    """

    name = Column(String, index=True, unique=True, nullable=False)
    key = Column(String, index=True, unique=True, nullable=False)
    description = Column(String, index=True, nullable=True)
    connection_type = Column(Enum(ConnectionType), nullable=False)
    access = Column(Enum(AccessLevel), nullable=False)
    secrets = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                CONFIG.security.app_encryption_key,
                AesGcmEngine,
                "pkcs5",
            )
        ),
        nullable=True,
    )  # Type bytea in the db
    last_test_timestamp = Column(DateTime(timezone=True))
    last_test_succeeded = Column(Boolean)
    disabled = Column(Boolean, server_default="f", default=False)
    disabled_at = Column(DateTime(timezone=True))

    # only applicable to ConnectionConfigs of connection type saas
    saas_config = Column(
        MutableDict.as_mutable(JSONB), index=False, unique=False, nullable=True
    )

    access_manual_webhook = relationship(  # type: ignore[misc]
        "AccessManualWebhook",
        back_populates="connection_config",
        cascade="delete",
        uselist=False,
    )

    @classmethod
    def create_without_saving(
        cls: Type[ConnectionConfig], db: Session, *, data: dict[str, Any]
    ) -> ConnectionConfig:
        """Create a ConnectionConfig without persisting to the database"""
        # Build properly formatted key/name for ConnectionConfig.
        # Borrowed from OrmWrappedFidesBase.create
        if hasattr(cls, "key"):
            data["key"] = get_key_from_data(data, cls.__name__)
            if db.query(cls).filter_by(key=data["key"]).first():
                raise KeyOrNameAlreadyExists(
                    f"Key {data['key']} already exists in {cls.__name__}. Keys will be snake-cased names if not provided. "
                    f"If you are seeing this error without providing a key, please provide a key or a different name."
                    ""
                )

        if hasattr(cls, "name"):
            data["name"] = data.get("name")
            if db.query(cls).filter_by(name=data["name"]).first():
                raise KeyOrNameAlreadyExists(
                    f"Name {data['name']} already exists in {cls.__name__}."
                )

        # Create
        db_obj = cls(**data)  # type: ignore
        return db_obj

    def get_saas_config(self) -> Optional[SaaSConfig]:
        """Returns a SaaSConfig object from a yaml config"""
        return SaaSConfig(**self.saas_config) if self.saas_config else None

    def update_saas_config(
        self,
        db: Session,
        saas_config: SaaSConfig,
    ) -> None:
        """
        Updates the SaaS config and initializes any empty secrets with
        connector param default values if available (will not override any existing secrets)
        """
        default_secrets = {
            connector_param.name: connector_param.default_value
            for connector_param in saas_config.connector_params
            if connector_param.default_value
        }
        updated_secrets = {**default_secrets, **(self.secrets or {})}
        self.secrets = updated_secrets
        self.saas_config = saas_config.dict()
        self.save(db)

    def update_test_status(
        self, test_status: ConnectionTestStatus, db: Session
    ) -> None:
        """Updates last_test_timestamp and last_test_succeeded after an attempt to make a test connection.

        If the test was skipped, for example, on an HTTP Connector, don't update these fields.
        """
        if test_status == ConnectionTestStatus.skipped:
            return

        self.last_test_timestamp = datetime.now()
        self.last_test_succeeded = test_status == ConnectionTestStatus.succeeded
        self.save(db)

    def delete(self, db: Session) -> Optional[Base]:
        """Hard deletes datastores that map this ConnectionConfig."""
        for dataset in self.datasets:
            dataset.delete(db=db)

        return super().delete(db=db)


@event.listens_for(ConnectionConfig.disabled, "set")
def connection_config_disabled_set(
    target: ConnectionConfig, value: bool, original_value: bool, _: Any
) -> None:
    """Update ConnectionConfig.disabled_at if ConnectionConfig.disabled changes"""
    if value != original_value:
        target.disabled_at = datetime.utcnow() if value else None
