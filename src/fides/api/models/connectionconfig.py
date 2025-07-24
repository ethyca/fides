from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional, Type

from loguru import logger
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, event
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import RelationshipProperty, Session, relationship
from sqlalchemy_utils.types.encrypted.encrypted_type import (
    AesGcmEngine,
    StringEncryptedType,
)

from fides.api.common_exceptions import KeyOrNameAlreadyExists
from fides.api.db.base_class import Base, FidesBase, JSONTypeOverride
from fides.api.models.consent_automation import ConsentAutomation
from fides.api.models.sql_models import System  # type: ignore[attr-defined]
from fides.api.schemas.policy import ActionType
from fides.api.schemas.saas.saas_config import SaaSConfig
from fides.config import CONFIG

if TYPE_CHECKING:
    from fides.api.models.detection_discovery.core import MonitorConfig
    from fides.api.schemas.connection_configuration.enums.system_type import SystemType


class ConnectionTestStatus(enum.Enum):
    """Enum for supplying statuses of validating credentials for a Connection Config to the user"""

    succeeded = "succeeded"
    failed = "failed"
    skipped = "skipped"


class ConnectionType(enum.Enum):
    """
    Supported types to which we can connect Fides.
    """

    attentive_email = "attentive_email"
    bigquery = "bigquery"
    datahub = "datahub"
    dynamodb = "dynamodb"
    fides = "fides"
    generic_consent_email = "generic_consent_email"  # Run after the traversal
    generic_erasure_email = "generic_erasure_email"  # Run after the traversal
    dynamic_erasure_email = "dynamic_erasure_email"  # Run after the traversal
    google_cloud_sql_mysql = "google_cloud_sql_mysql"
    google_cloud_sql_postgres = "google_cloud_sql_postgres"
    https = "https"
    manual = "manual"  # Deprecated - use manual_webhook instead
    manual_webhook = "manual_webhook"  # Runs upfront before the traversal
    manual_task = "manual_task"  # Manual task integration
    mariadb = "mariadb"
    mongodb = "mongodb"
    mssql = "mssql"
    mysql = "mysql"
    okta = "okta"
    postgres = "postgres"
    rds_mysql = "rds_mysql"
    rds_postgres = "rds_postgres"
    redshift = "redshift"
    s3 = "s3"
    saas = "saas"
    scylla = "scylla"
    snowflake = "snowflake"
    sovrn = "sovrn"
    timescale = "timescale"
    website = "website"
    # Test connection types, used for testing purposes only
    test_website = "test_website"  # used for ConfigurableTesteWebsiteMonitor

    @property
    def human_readable(self) -> str:
        """Human-readable mapping for ConnectionTypes
        Add to this mapping if you add a new ConnectionType
        """
        readable_mapping: dict[str, str] = {
            ConnectionType.attentive_email.value: "Attentive Email",
            ConnectionType.bigquery.value: "BigQuery",
            ConnectionType.datahub.value: "DataHub",
            ConnectionType.dynamic_erasure_email.value: "Dynamic Erasure Email",
            ConnectionType.dynamodb.value: "DynamoDB",
            ConnectionType.fides.value: "Fides Connector",
            ConnectionType.generic_consent_email.value: "Generic Consent Email",
            ConnectionType.generic_erasure_email.value: "Generic Erasure Email",
            ConnectionType.google_cloud_sql_mysql.value: "Google Cloud SQL for MySQL",
            ConnectionType.google_cloud_sql_postgres.value: "Google Cloud SQL for Postgres",
            ConnectionType.https.value: "Policy Webhook",
            ConnectionType.manual_webhook.value: "Manual Process",
            ConnectionType.manual_task.value: "Manual Task",
            ConnectionType.manual.value: "Manual Connector",
            ConnectionType.mariadb.value: "MariaDB",
            ConnectionType.mongodb.value: "MongoDB",
            ConnectionType.mssql.value: "Microsoft SQL Server",
            ConnectionType.mysql.value: "MySQL",
            ConnectionType.okta.value: "Okta",
            ConnectionType.postgres.value: "PostgreSQL",
            ConnectionType.rds_mysql.value: "RDS MySQL",
            ConnectionType.rds_postgres.value: "RDS Postgres",
            ConnectionType.redshift.value: "Amazon Redshift",
            ConnectionType.s3.value: "Amazon S3",
            ConnectionType.saas.value: "SaaS",
            ConnectionType.scylla.value: "Scylla DB",
            ConnectionType.snowflake.value: "Snowflake",
            ConnectionType.sovrn.value: "Sovrn",
            ConnectionType.timescale.value: "TimescaleDB",
            ConnectionType.website.value: "Website",
            ConnectionType.test_website.value: "Test Website Connector -- not for production use",
        }
        try:
            return readable_mapping[self.value]
        except KeyError:
            raise NotImplementedError(
                "Add new ConnectionType to human_readable mapping"
            )

    @property
    def system_type(self) -> "SystemType":
        from fides.api.schemas.connection_configuration.enums.system_type import (
            SystemType,
        )

        system_type_mapping: dict[str, SystemType] = {
            ConnectionType.attentive_email.value: SystemType.email,
            ConnectionType.bigquery.value: SystemType.database,
            ConnectionType.datahub.value: SystemType.data_catalog,
            ConnectionType.dynamic_erasure_email.value: SystemType.email,
            ConnectionType.dynamodb.value: SystemType.database,
            ConnectionType.fides.value: SystemType.manual,
            ConnectionType.generic_consent_email.value: SystemType.email,
            ConnectionType.generic_erasure_email.value: SystemType.email,
            ConnectionType.google_cloud_sql_mysql.value: SystemType.database,
            ConnectionType.google_cloud_sql_postgres.value: SystemType.database,
            ConnectionType.https.value: SystemType.manual,
            ConnectionType.manual_webhook.value: SystemType.manual,
            ConnectionType.manual_task.value: SystemType.manual,
            ConnectionType.manual.value: SystemType.manual,
            ConnectionType.mariadb.value: SystemType.database,
            ConnectionType.mongodb.value: SystemType.database,
            ConnectionType.mssql.value: SystemType.database,
            ConnectionType.mysql.value: SystemType.database,
            ConnectionType.okta.value: SystemType.system,
            ConnectionType.postgres.value: SystemType.database,
            ConnectionType.rds_mysql.value: SystemType.database,
            ConnectionType.rds_postgres.value: SystemType.database,
            ConnectionType.redshift.value: SystemType.database,
            ConnectionType.s3.value: SystemType.database,
            ConnectionType.saas.value: SystemType.saas,
            ConnectionType.scylla.value: SystemType.database,
            ConnectionType.snowflake.value: SystemType.database,
            ConnectionType.sovrn.value: SystemType.email,
            ConnectionType.timescale.value: SystemType.database,
            ConnectionType.website.value: SystemType.website,
            ConnectionType.test_website.value: SystemType.website,
        }

        try:
            return system_type_mapping[self.value]
        except KeyError:
            raise NotImplementedError("Add new ConnectionType to system_type mapping")


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

    name = Column(String, nullable=True)
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
    )  # Type bytes in the db
    last_test_timestamp = Column(DateTime(timezone=True))
    last_test_succeeded = Column(Boolean)
    disabled = Column(Boolean, server_default="f", default=False)
    disabled_at = Column(DateTime(timezone=True))

    # Optional column to store the last time the connection was "ran"
    # Each integration can determine the semantics of what "being run" is
    last_run_timestamp = Column(DateTime(timezone=True), nullable=True)

    # only applicable to ConnectionConfigs of connection type saas
    saas_config = Column(
        MutableDict.as_mutable(JSONB), index=False, unique=False, nullable=True
    )

    system_id = Column(
        String, ForeignKey(System.id_field_path), nullable=True, index=True
    )

    datasets = relationship(  # type: ignore[misc]
        "DatasetConfig",
        back_populates="connection_config",
        cascade="all, delete",
    )

    # Monitor configs related to this connection config.
    # If the connection config is deleted, the monitor configs will be deleted as well.
    monitors: RelationshipProperty[List["MonitorConfig"]] = relationship(
        "MonitorConfig",
        back_populates="connection_config",
        cascade="all, delete",
    )

    access_manual_webhook = relationship(  # type: ignore[misc]
        "AccessManualWebhook",
        back_populates="connection_config",
        cascade="delete",
        uselist=False,
    )

    manual_task = relationship(  # type: ignore[misc]
        "ManualTask",
        primaryjoin="and_(ConnectionConfig.id == foreign(ManualTask.parent_entity_id), "
        "ManualTask.parent_entity_type == 'connection_config')",
        cascade="delete",
        uselist=False,
    )

    pre_approval_webhooks = relationship(  # type: ignore[misc]
        "PreApprovalWebhook",
        back_populates="connection_config",
        cascade="delete",
    )

    system = relationship(System, back_populates="connection_configs", uselist=False)

    consent_automation: RelationshipProperty[Optional[ConsentAutomation]] = (
        relationship(ConsentAutomation, uselist=False, cascade="all, delete-orphan")
    )

    # Identifies the privacy actions needed from this connection by the associated system.
    enabled_actions = Column(
        ARRAY(Enum(ActionType, native_enum=False)), unique=False, nullable=True
    )

    @property
    def system_key(self) -> Optional[str]:
        """Property for caching a system identifier for systems (or connector names as a fallback) for consent reporting"""
        if self.system:
            return self.system.fides_key
        # TODO: Remove this fallback once all connection configs are linked to systems
        # This will always be None in the future. `self.system` will always be set.
        return self.name

    @property
    def authorized(self) -> bool:
        """Returns True if the connection config has an access token, used for OAuth2 connections"""

        saas_config = self.get_saas_config()
        if not saas_config:
            return False

        authentication = saas_config.client_config.authentication
        if not authentication:
            return False

        # hard-coding to avoid cyclic dependency
        if authentication.strategy not in [
            "oauth2_authorization_code",
            "oauth2_client_credentials",
        ]:
            return False

        return bool(self.secrets and "access_token" in self.secrets.keys())

    @property
    def name_or_key(self) -> str:
        """Returns the ConnectionConfig name if it exists, or its key otherwise."""
        return self.name or self.key

    @classmethod
    def create_without_saving(
        cls: Type[ConnectionConfig], db: Session, *, data: dict[str, Any]
    ) -> ConnectionConfig:
        """Create a ConnectionConfig without persisting to the database"""
        # Build properly formatted key/name for ConnectionConfig.
        # Borrowed from OrmWrappedFidesBase.create
        if hasattr(cls, "key"):
            if db.query(cls).filter_by(key=data["key"]).first():
                raise KeyOrNameAlreadyExists(
                    f"Key {data['key']} already exists in {cls.__name__}. Keys will be snake-cased names if not provided. "
                    f"If you are seeing this error without providing a key, please provide a key or a different name."
                    ""
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
        self.saas_config = saas_config.model_dump(mode="json")
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

    def delete(self, db: Session) -> Optional[FidesBase]:
        """Hard deletes datastores that map this ConnectionConfig."""
        logger.info(
            "Deleting connection config {}...",
            self.key,
        )
        for dataset in self.datasets:
            dataset.delete(db=db)

        for monitor in self.monitors:
            logger.info(
                "Deleting monitor config {} associated with connection config {}...",
                monitor.key,
                self.key,
            )
            monitor.delete(db=db)

        return super().delete(db=db)


@event.listens_for(ConnectionConfig.disabled, "set")
def connection_config_disabled_set(
    target: ConnectionConfig, value: bool, original_value: bool, _: Any
) -> None:
    """Update ConnectionConfig.disabled_at if ConnectionConfig.disabled changes"""
    if value != original_value:
        target.disabled_at = datetime.utcnow() if value else None
