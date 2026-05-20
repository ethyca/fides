from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import Field

from fides.api.schemas.base_class import FidesSchema


class Reachability(str, Enum):
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"
    REQUIRES_MANUAL_IDENTITY = "requires_manual_identity"


class ActionStatus(str, Enum):
    ACTIVE = "active"
    SKIPPED = "skipped"


class FieldDetail(FidesSchema):
    name: str
    data_categories: list[str] = Field(default_factory=list)
    is_identity: bool = False


class CollectionDetail(FidesSchema):
    name: str
    fields: list[FieldDetail] = Field(default_factory=list)


class DatasetDetail(FidesSchema):
    fides_key: str
    collections: list[CollectionDetail] = Field(default_factory=list)


class SystemRef(FidesSchema):
    fides_key: str
    name: str
    data_uses: list[str] = Field(default_factory=list)


class CollectionCount(FidesSchema):
    traversed: int
    total: int


class IntegrationNode(FidesSchema):
    id: str  # "integration:<connection_key>"
    connection_key: str
    connector_type: str
    saas_type: str | None = None
    system: SystemRef | None = None
    reachability: Reachability
    action_status: ActionStatus
    collection_count: CollectionCount
    data_categories: list[str] = Field(default_factory=list)
    datasets: list[DatasetDetail] = Field(default_factory=list)


class Assignee(FidesSchema):
    type: Literal["user", "team"]
    name: str


class ManualTaskField(FidesSchema):
    name: str
    type: str
    label: str | None = None
    help_text: str | None = None
    required: bool = False


class ManualTaskCondition(FidesSchema):
    summary: str
    expression: str


class ManualTaskNode(FidesSchema):
    id: str  # "manual:<task_key>"
    name: str
    assignees: list[Assignee] = Field(default_factory=list)
    fields: list[ManualTaskField] = Field(default_factory=list)
    conditions: list[ManualTaskCondition] = Field(default_factory=list)
    gates: list[str] = Field(default_factory=list)


class PrivacyCenterFormRef(FidesSchema):
    id: str
    name: str
    url_path: str


class IdentityRoot(FidesSchema):
    id: Literal["identity-root"] = "identity-root"
    identity_types: list[str] = Field(default_factory=list)
    privacy_center_forms: list[PrivacyCenterFormRef] = Field(default_factory=list)


class PreviewEdge(FidesSchema):
    source: str
    target: str
    kind: Literal["depends_on", "gates"]
    dep_count: int | None = None  # only set for "depends_on"


class TraversalPreview(FidesSchema):
    """Structured preview of a property-scoped DSR traversal — no property/cache metadata."""

    action_type: Literal["access", "erasure"]
    identity_root: IdentityRoot
    integrations: list[IntegrationNode] = Field(default_factory=list)
    manual_tasks: list[ManualTaskNode] = Field(default_factory=list)
    edges: list[PreviewEdge] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
