from __future__ import annotations

from datetime import datetime
from enum import Enum
from re import match
from typing import Any, Dict, Iterable, List, Optional, Set, Type

from loguru import logger
from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.future import select
from sqlalchemy.orm import RelationshipProperty, Session, relationship, validates
from sqlalchemy.orm.query import Query

from fides.api.db.base_class import Base, FidesBase
from fides.api.models.connectionconfig import ConnectionConfig
from fides.api.models.detection_discovery.staged_resource_error import (
    StagedResourceError,
)
from fides.api.models.sql_models import System  # type: ignore[attr-defined]


class DiffStatus(Enum):
    ADDITION = "addition"
    REMOVAL = "removal"
    CLASSIFICATION_ADDITION = "classification_addition"
    CLASSIFICATION_UPDATE = "classification_update"
    MONITORED = "monitored"
    MUTED = "muted"


class MonitorFrequency(Enum):
    """
    Enum representing monitor frequency. Not used in DB but needed for translating to API schema
    """

    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"
    NOT_SCHEDULED = "Not scheduled"


# pattern for a string of 4 comma-separated integers,
# used to represent the months of the year that the monitor will run
# on quarterly basis, in cron format
QUARTERLY_MONTH_PATTERN = r"^\d+,\d+,\d+,\d+$"


class StagedResourceType(str, Enum):
    """
    Enum representing the type of staged resource.
    The resource_type column is a string in the DB, this is just for
    application-level use.
    """

    # Note: If you add a new resource type, make sure to update either
    # get_datastore_resource_types or get_website_monitor_resource_types

    # Datastore staged resources
    DATABASE = "Database"
    SCHEMA = "Schema"
    TABLE = "Table"
    FIELD = "Field"
    ENDPOINT = "Endpoint"
    # Website monitor staged resources
    COOKIE = "Cookie"
    BROWSER_REQUEST = "Browser request"
    IMAGE_BROWSER_REQUEST = "Image"
    IFRAME_BROWSER_REQUEST = "iFrame"
    JAVASCRIPT_BROWSER_REQUEST = "Javascript tag"

    @staticmethod
    def get_datastore_resource_types() -> List["StagedResourceType"]:
        return [
            StagedResourceType.DATABASE,
            StagedResourceType.SCHEMA,
            StagedResourceType.TABLE,
            StagedResourceType.FIELD,
            StagedResourceType.ENDPOINT,
        ]

    @staticmethod
    def get_website_monitor_resource_types() -> List["StagedResourceType"]:
        return [
            StagedResourceType.COOKIE,
            StagedResourceType.BROWSER_REQUEST,
            StagedResourceType.IMAGE_BROWSER_REQUEST,
            StagedResourceType.IFRAME_BROWSER_REQUEST,
            StagedResourceType.JAVASCRIPT_BROWSER_REQUEST,
        ]

    def is_datastore_resource(self) -> bool:
        return self in self.get_datastore_resource_types()

    def is_website_monitor_resource(self) -> bool:
        return self in self.get_website_monitor_resource_types()


class SharedMonitorConfig(Base, FidesBase):
    """SQL model for shareable monitor configurations"""

    @declared_attr
    def __tablename__(self) -> str:
        return "shared_monitor_config"

    # Basic info
    name = Column(String, nullable=False)
    key = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    # Classification parameters (including regex patterns)
    classify_params = Column(
        MutableDict.as_mutable(JSONB),
        index=False,
        unique=False,
        nullable=False,
        server_default="{}",
        default=dict,
    )


class MonitorConfig(Base):
    """
    Monitor configuration used for data detection and discovery.

    Each monitor configuration references `ConnectionConfig`, which provide it with underlying
    configuration details used in connecting to the external data store.
    """

    name = Column(String, nullable=True)
    key = Column(String, index=True, unique=True, nullable=False)
    connection_config_id = Column(
        String,
        ForeignKey(ConnectionConfig.id_field_path),
        nullable=False,
        index=True,
    )
    databases = Column(
        ARRAY(String),
        index=False,
        unique=False,
        nullable=False,
        server_default="{}",
        default=dict,
    )  # the databases to which the monitor is scoped
    excluded_databases = Column(
        ARRAY(String),
        index=False,
        unique=False,
        nullable=False,
        server_default="{}",
        default=dict,
    )  # the databases to which the monitor is not scoped
    monitor_execution_trigger = Column(
        MutableDict.as_mutable(JSONB),
        index=False,
        unique=False,
        nullable=True,
    )  # stores the cron-based kwargs for scheduling the monitor execution.
    # see https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html

    # We use _classify_params for the actual column to prevent direct access
    _classify_params = Column(
        "classify_params",
        MutableDict.as_mutable(JSONB),
        index=False,
        unique=False,
        nullable=True,
    )  # parameters that the monitor will use for classification execution

    datasource_params = Column(
        MutableDict.as_mutable(JSONB),
        index=False,
        unique=False,
        nullable=True,
    )  # monitor parameters that are specific per datasource
    # these are held as an untyped JSON dict (in the DB) to stay flexible

    last_monitored = Column(
        DateTime(timezone=True),
        nullable=True,
    )  # when the monitor was last executed

    enabled = Column(
        Boolean,
        default=True,
        nullable=False,
        server_default="t",
    )

    # TODO: many-to-many link to users assigned as data stewards; likely will need a join-table

    connection_config = relationship(ConnectionConfig)

    executions = relationship(
        "MonitorExecution",
        cascade="all, delete-orphan",
        backref="monitor_config",
        primaryjoin="MonitorExecution.monitor_config_key == foreign(MonitorConfig.key)",
        single_parent=True,
    )

    shared_config_id = Column(
        String,
        ForeignKey(SharedMonitorConfig.id_field_path, ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    shared_config = relationship(SharedMonitorConfig)

    __table_args__ = (
        CheckConstraint(  # type: ignore
            "key NOT LIKE '%.%'", name="ck_monitorconfig_key_no_dots"
        ),
    )

    @property
    def classify_params(self) -> dict:
        """
        Returns the merged classify parameters from both the monitor config and
        the shared config (if it exists).

        The shared config parameters take precedence over the monitor's own parameters,
        but only for values that are not falsy (None, empty, etc.).
        """
        # Start with an empty dict
        merged_params = {}

        # Add this monitor's params if available
        if self._classify_params:
            merged_params.update(self._classify_params)

        # Add/override with shared config params if available
        if self.shared_config and self.shared_config.classify_params:
            # Only update with non-falsy values from shared config
            for key, value in self.shared_config.classify_params.items():
                if value:  # Only override if the value is not falsy
                    merged_params[key] = value

        return merged_params

    @classify_params.setter
    def classify_params(self, value: Dict[str, Any]) -> None:
        """Setter for the classify_params to maintain compatibility with existing code"""
        self._classify_params = value

    @property
    def connection_config_key(self) -> str:
        """Derives the `connection_config_key`"""
        return self.connection_config.key

    @property
    def execution_start_date(self) -> Optional[datetime]:
        """Derives the `execution_start_date`"""
        if (
            not self.monitor_execution_trigger
            or self.monitor_execution_trigger.get("start_date", None) is None
        ):
            return None
        return self.monitor_execution_trigger.get("start_date")

    @property
    def execution_frequency(self) -> Optional[MonitorFrequency]:
        """Derives the `execution_frequency`"""
        if (
            not self.monitor_execution_trigger
            or self.monitor_execution_trigger.get("hour", None) is None
        ):
            return MonitorFrequency.NOT_SCHEDULED
        month_trigger = self.monitor_execution_trigger.get("month", None)
        if month_trigger is not None:
            if isinstance(month_trigger, str) and match(
                QUARTERLY_MONTH_PATTERN, month_trigger
            ):
                return MonitorFrequency.QUARTERLY
            return MonitorFrequency.YEARLY
        if self.monitor_execution_trigger.get("day", None) is not None:
            return MonitorFrequency.MONTHLY
        if self.monitor_execution_trigger.get("day_of_week", None) is not None:
            return MonitorFrequency.WEEKLY
        return MonitorFrequency.DAILY

    def update(self, db: Session, *, data: dict[str, Any]) -> FidesBase:
        """
        Override the base class `update` to validate database include/exclude
        and derive the `execution_trigger` dict field
        """
        MonitorConfig.database_include_exclude_list_is_valid(data)
        MonitorConfig.derive_execution_trigger_dict(data)
        return super().update(db=db, data=data)

    @classmethod
    def database_include_exclude_list_is_valid(cls, data: Dict[str, Any]) -> None:
        """Check that both include and exclude have not both been set"""
        include = data.get("databases", [])
        exclude = data.get("excluded_databases", [])
        if include and exclude:
            raise ValueError(
                "Both `databases` and `excluded_databases` cannot be set at the same time."
            )

    @classmethod
    def create(
        cls: Type[MonitorConfig],
        db: Session,
        *,
        data: dict[str, Any],
        check_name: bool = True,
    ) -> MonitorConfig:
        """
        Override the base class `create` to validate database include/exclude
        and derive the `execution_trigger` dict field
        """
        MonitorConfig.database_include_exclude_list_is_valid(data)
        MonitorConfig.derive_execution_trigger_dict(data)
        return super().create(db=db, data=data, check_name=check_name)

    @staticmethod
    def derive_execution_trigger_dict(data: Dict[str, Any]) -> None:
        """
        Determines the execution trigger (cron) dict based on the
        corresponding schema properties provided in the `data` dict.

        The `data` dict is updated in place with the execution trigger dict
        placed in the `monitor_execution_trigger` key, if applicable, and with the
        `execution_frequency` and `execution_start_date` keys removed.

        The `execution_start_date` is inferred as the basis for the day and time
        for repeated monitor execution, and the frequency of execution is based
        on the `execution_frequency` field.

        For example, an `execution_start_date` of "2024-05-14 12:00:00+00:00":
        - with an `execution_frequency` of "daily", it will result in daily
        execution at 12:00:00+00:00;
        - with an `execution_frequency` of "weekly", it will result in weekly
        execution at 12:00:00+00:00 on every Tuesday, since 2024-05-14 is
        a Tuesday.
        - with an `execution_frequency` of "monthly", it will result in monthly
        execution at 12:00:00+00:00 on the 14th day of every month.
        - with an `execution_frequency` of "quarterly", it will result in quarterly
        execution at 12:00:00+00:00 on the 14th day of the first month of each quarter.
        - with an `execution_frequency` of "yearly", it will result in yearly
        execution at 12:00:00+00:00 on May 14th of each year.

        See https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html
        for more information about the cron trigger parameters.
        """
        execution_frequency = data.pop("execution_frequency", None)
        execution_start_date = data.pop("execution_start_date", None)
        if execution_frequency == MonitorFrequency.NOT_SCHEDULED:
            data["monitor_execution_trigger"] = None
            return
        if execution_frequency and execution_start_date:
            cron_trigger_dict = {}
            cron_trigger_dict["start_date"] = execution_start_date
            cron_trigger_dict["timezone"] = execution_start_date.tzinfo
            cron_trigger_dict["hour"] = execution_start_date.hour
            cron_trigger_dict["minute"] = execution_start_date.minute
            cron_trigger_dict["second"] = execution_start_date.second
            if execution_frequency == MonitorFrequency.WEEKLY:
                cron_trigger_dict["day_of_week"] = execution_start_date.weekday()
            if execution_frequency == MonitorFrequency.MONTHLY:
                cron_trigger_dict["day"] = execution_start_date.day
            if execution_frequency == MonitorFrequency.QUARTERLY:
                cron_trigger_dict["day"] = execution_start_date.day
                # Calculate which month of the quarter (0-2) this is
                month_of_quarter = (execution_start_date.month - 1) % 3
                # Set to run in the same month of each quarter (1, 4, 7, 10 for first month)
                cron_trigger_dict["month"] = (
                    f"{1 + month_of_quarter},{4 + month_of_quarter},{7 + month_of_quarter},{10 + month_of_quarter}"
                )
            if execution_frequency == MonitorFrequency.YEARLY:
                cron_trigger_dict["day"] = execution_start_date.day
                cron_trigger_dict["month"] = execution_start_date.month
            data["monitor_execution_trigger"] = cron_trigger_dict

    @validates("key")
    def validate_key_no_dots(self, _key: str, value: str) -> str:
        if value and "." in value:
            raise ValueError('MonitorConfig.key cannot contain "." characters')
        return value


class StagedResourceAncestor(Base):
    """
    A simple junction table that is used to store the many-to-many relationship
    between staged resources and their ancestors.

    This table is used to easily lookup all ancestors of a given staged resource,
    as its indexed by both ancestor and descendant URN columns.

    Its entries should be deleted when the staged resource is deleted, via cascade.
    """

    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    ancestor_urn = Column(
        String,
        ForeignKey("stagedresource.urn", ondelete="CASCADE"),
        nullable=False,
    )
    descendant_urn = Column(
        String,
        ForeignKey("stagedresource.urn", ondelete="CASCADE"),
        nullable=False,
    )

    ancestor_staged_resource = relationship(
        "StagedResource",
        back_populates="ancestor_links",
        lazy="selectin",
        foreign_keys=[ancestor_urn],
    )
    descendant_staged_resource = relationship(
        "StagedResource",
        back_populates="descendant_links",
        lazy="selectin",
        foreign_keys=[descendant_urn],
    )

    __table_args__ = (
        UniqueConstraint(
            "ancestor_urn", "descendant_urn", name="uq_staged_resource_ancestor"
        ),
        Index("ix_staged_resource_ancestor_pkey", "id", unique=True),
        Index("ix_staged_resource_ancestor_ancestor", "ancestor_urn"),
        Index("ix_staged_resource_ancestor_descendant", "descendant_urn"),
    )

    @classmethod
    def create_all_staged_resource_ancestor_links(
        cls,
        db: Session,
        ancestor_links: Dict[str, Set[str]],
        batch_size: int = 10000,  # Conservative batch size
    ) -> None:
        """
        Bulk inserts all entries in the StagedResourceAncestor table
        based on the provided mapping of descendant URNs to their ancestor URN sets.

        We execute the bulk INSERT with the provided (synchronous) db session,
        but the transaction is _not_ committed, so the caller must commit the transaction
        to persist the changes.

        Uses batching to handle large datasets without hitting PostgreSQL parameter limits.

        Args:
            db: Database session
            ancestor_links: Dict mapping descendant URNs to sets of ancestor URNs
        """
        stmt_text = text(
            """
            INSERT INTO stagedresourceancestor (id, ancestor_urn, descendant_urn)
            VALUES ('srl_' || gen_random_uuid(), :ancestor_urn, :descendant_urn)
            ON CONFLICT (ancestor_urn, descendant_urn) DO NOTHING;
            """
        )

        current_batch = []

        for descendant_urn, ancestor_urns in ancestor_links.items():
            if ancestor_urns:  # Only create links if there are ancestors
                for ancestor_urn in ancestor_urns:
                    current_batch.append(
                        {"ancestor_urn": ancestor_urn, "descendant_urn": descendant_urn}
                    )

                    # Execute batch when it reaches the desired size
                    if len(current_batch) >= batch_size:
                        logger.debug(
                            f"Inserting batch of {len(current_batch)} staged resource ancestor links"
                        )
                        db.execute(stmt_text, current_batch)
                        current_batch = []

        # Execute any remaining items in the final batch
        if current_batch:
            logger.debug(
                f"Inserting batch of {len(current_batch)} staged resource ancestor links"
            )
            db.execute(stmt_text, current_batch)


class StagedResource(Base):
    """
    Base DB model that represents a staged resource, fields common to all types of staged resources
    """

    name = Column(String, nullable=True)
    urn = Column(String, index=True, unique=True, nullable=False)
    resource_type = Column(String, index=True, nullable=True)
    description = Column(String, nullable=True)
    monitor_config_id = Column(
        String,
        index=True,  # indexed because we frequently need to slice by monitor config ID
        nullable=True,
    )  # just a "soft" pointer, for now TODO: make this a FK

    # for now, this is just used for web monitor resources.
    system_id = Column(
        String,
        ForeignKey(System.id_field_path),
        nullable=True,
        index=True,
    )

    # TODO: we should be able to enable the below relationship, but it
    # confuses different functionality since 'system' means different
    # things depending on whether the resource is a datastore or web monitor
    # staged resource
    #    system = relationship(System)

    # the Compass vendor ID associated with the StagedResource.
    # only used for web monitor resources
    vendor_id = Column(
        String,
        nullable=True,
        index=True,  # indexed because we frequently need to slice by vendor ID
    )

    source_modified = Column(
        DateTime(timezone=True),
        nullable=True,
    )  # when the resource was modified in the datasource
    classifications = Column(
        ARRAY(JSONB),
        nullable=False,
        server_default="{}",
        default=dict,
    )
    user_assigned_data_categories = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=dict,
    )
    # This field is intentionally nullable to distinguish the case when no user assigned data uses
    # have been set (default, value is None) from the case in which they have been explicitly set
    # as empty (value is empty array). This allows users to remove all data uses from a StagedResource,
    # which was not possible when this field was not nullable.
    user_assigned_data_uses = Column(
        ARRAY(String),
        nullable=True,
        server_default=None,
        default=None,
    )
    user_assigned_system_id = Column(String, nullable=True, index=True)

    # pointers to child and parent URNs
    children = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        default=dict,
    )
    parent = Column(String, nullable=True)

    # diff-related fields
    diff_status = Column(String, nullable=True, index=True)

    errors: RelationshipProperty[List[StagedResourceError]] = relationship(
        "StagedResourceError",
        foreign_keys=[StagedResourceError.staged_resource_urn],
        primaryjoin="StagedResource.urn == StagedResourceError.staged_resource_urn",
        cascade="all, delete-orphan",
    )

    ancestor_links: RelationshipProperty[List[StagedResourceAncestor]] = relationship(
        "StagedResourceAncestor",
        back_populates="descendant_staged_resource",
        lazy="dynamic",
        cascade="all, delete",
        foreign_keys=[StagedResourceAncestor.descendant_urn],
    )

    descendant_links: RelationshipProperty[List[StagedResourceAncestor]] = relationship(
        "StagedResourceAncestor",
        back_populates="ancestor_staged_resource",
        lazy="dynamic",
        cascade="all, delete",
        foreign_keys=[StagedResourceAncestor.ancestor_urn],
    )

    def ancestors(self, db: Session) -> List[StagedResource]:
        """
        Returns the ancestors of the staged resource
        """
        # Single query to get all ancestors with their data
        query = (
            select(StagedResource)
            .join(
                StagedResourceAncestor,
                StagedResource.urn == StagedResourceAncestor.ancestor_urn,
            )
            .where(StagedResourceAncestor.descendant_urn == self.urn)
        )

        result = db.execute(query)
        return list(result.scalars().all())

    def descendants(self, db: Session) -> List[StagedResource]:
        """
        Returns the descendants of the staged resource
        """
        # Single query to get all descendants with their data
        query = (
            select(StagedResource)
            .join(
                StagedResourceAncestor,
                StagedResource.urn == StagedResourceAncestor.descendant_urn,
            )
            .where(StagedResourceAncestor.ancestor_urn == self.urn)
        )

        result = db.execute(query)
        return list(result.scalars().all())

    # placeholder for additional attributes
    meta = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        server_default="{}",
        default=dict,
    )

    data_uses = Column(
        ARRAY(String),
        nullable=True,
        server_default="{}",
        default=dict,
    )

    __table_args__ = (
        # Used for querying monitor aggregates
        Index(
            "ix_stagedresource_monitor_config_resource_type_consent",
            "monitor_config_id",
            "resource_type",
            text("(meta->>'consent_aggregated')"),
        ),
        # Used for querying system aggregates
        Index(
            "ix_stagedresource_system_vendor_consent",
            "system_id",
            "vendor_id",
            text("(meta->>'consent_aggregated')"),
        ),
        # GIN indices for array operations (&&, @>, <@)
        Index(
            "idx_stagedresource_classifications_gin",
            "classifications",
            postgresql_using="gin",
        ),
        Index(
            "idx_stagedresource_user_categories_gin",
            "user_assigned_data_categories",
            postgresql_using="gin",
        ),
    )

    @classmethod
    def get_urn(cls, db: Session, urn: str) -> Optional[StagedResource]:
        """Utility to retrieve the staged resource with the given URN"""
        return cls.get_by(db=db, field="urn", value=urn)

    @classmethod
    def get_urn_list(cls, db: Session, urns: Iterable[str]) -> Iterable[StagedResource]:
        """
        Utility to retrieve all staged resources with the given URNs
        """
        results = db.execute(select(StagedResource).where(StagedResource.urn.in_(urns)))
        return results.scalars().all()

    @classmethod
    async def get_urn_async(
        cls, db: AsyncSession, urn: str
    ) -> Optional[StagedResource]:
        """
        Utility to retrieve the staged resource with the given URN using an async session
        """
        results = await db.execute(
            select(StagedResource).where(StagedResource.urn == urn)
        )
        return results.scalars().first()

    @classmethod
    async def get_urn_list_async(
        cls, db: AsyncSession, urns: List[str]
    ) -> Optional[List[StagedResource]]:
        """
        Utility to retrieve the staged resource with the given URN using an async session
        """
        results = await db.execute(
            select(StagedResource).where(StagedResource.urn.in_(urns))
        )
        return results.scalars().all()

    def mark_as_addition(
        self,
        db: Session,
        parent_resource_urns: Iterable[str] = [],
    ) -> None:
        """
        Marks the resource as an addition
        """
        self.diff_status = DiffStatus.ADDITION.value


class MonitorExecution(Base):
    """
    Monitor execution record used for data detection and discovery.

    Each monitor execution references `MonitorConfig`, which provide it with underlying
    configuration details used in connecting to the external data store.
    """

    # redefined here because there's a minor, unintended discrepancy between
    # this `id` field and that of the `Base` class, which explicitly sets `index=True`.
    # TODO: we likely should _not_ be setting `index=True` on the `id`
    # attribute of the `Base` class, as `primary_key=True` already specifies a
    # primary key constraint, which will implicitly create an index for the field.
    id = Column(String(255), primary_key=True, default=FidesBase.generate_uuid)

    monitor_config_key = Column(String, nullable=False, index=True)
    status = Column(String, nullable=True)
    started = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )
    completed = Column(DateTime(timezone=True), nullable=True)
    classification_instances = Column(
        ARRAY(String),
        index=False,
        unique=False,
        nullable=False,
        default=list,
    )
    # stores additional information from monitor execution failures as an array of strings,
    # e.g. error messages, stack traces, etc.
    messages = Column(
        ARRAY(String),
        nullable=False,
        default=list,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


def fetch_staged_resources_by_type_query(
    resource_type: str,
    monitor_config_ids: Optional[List[str]] = None,
    show_hidden: bool = False,
) -> Query[StagedResource]:
    """
    Fetches staged resources by type and monitor config ID. Optionally filters out muted staged resources ("hidden").
    """
    logger.info(
        f"Fetching staged resources of type {resource_type}, show_hidden={show_hidden}, monitor_config_ids={monitor_config_ids}"
    )
    query = select(StagedResource).where(StagedResource.resource_type == resource_type)

    if monitor_config_ids:
        query = query.filter(StagedResource.monitor_config_id.in_(monitor_config_ids))
    if not show_hidden:
        from sqlalchemy import or_

        query = query.filter(
            or_(
                StagedResource.diff_status != DiffStatus.MUTED.value,
                StagedResource.diff_status.is_(None),
            )
        )

    return query
