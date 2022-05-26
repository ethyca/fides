from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fidesops.core.config import config
from fidesops.db.base_class import Base, JSONTypeOverride
from fidesops.schemas.saas.saas_config import SaaSConfig


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
    manual = "manual"


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
    connection_type = Column(Enum(ConnectionType), nullable=False)
    access = Column(Enum(AccessLevel), nullable=False)
    secrets = Column(
        MutableDict.as_mutable(
            StringEncryptedType(
                JSONTypeOverride,
                config.security.APP_ENCRYPTION_KEY,
                AesGcmEngine,
                "pkcs5",
            )
        ),
        nullable=True,
    )  # Type bytea in the db
    last_test_timestamp = Column(DateTime(timezone=True))
    last_test_succeeded = Column(Boolean)

    # only applicable to ConnectionConfigs of connection type saas
    saas_config = Column(
        MutableDict.as_mutable(JSONB), index=False, unique=False, nullable=True
    )

    def get_saas_config(self) -> Optional[SaaSConfig]:
        """Returns a SaaSConfig object from a yaml config"""
        return SaaSConfig(**self.saas_config) if self.saas_config else None

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
