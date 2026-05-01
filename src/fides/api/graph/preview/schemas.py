from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

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
    data_categories: List[str] = Field(default_factory=list)
    is_identity: bool = False


class CollectionDetail(FidesSchema):
    name: str
    skipped: bool = False
    fields: List[FieldDetail] = Field(default_factory=list)


class DatasetDetail(FidesSchema):
    fides_key: str
    collections: List[CollectionDetail] = Field(default_factory=list)


class SystemRef(FidesSchema):
    fides_key: str
    name: str
    data_use: Optional[str] = None


class CollectionCount(FidesSchema):
    traversed: int
    total: int


class IntegrationNode(FidesSchema):
    id: str  # "integration:<connection_key>"
    connection_key: str
    connector_type: str
    system: Optional[SystemRef] = None
    reachability: Reachability
    action_status: ActionStatus
    collection_count: CollectionCount
    data_categories: List[str] = Field(default_factory=list)
    datasets: List[DatasetDetail] = Field(default_factory=list)


class Assignee(FidesSchema):
    type: Literal["user", "team"]
    name: str


class ManualTaskField(FidesSchema):
    name: str
    type: str
    label: Optional[str] = None
    help_text: Optional[str] = None
    required: bool = False


class ManualTaskCondition(FidesSchema):
    summary: str
    expression: str


class ManualTaskNode(FidesSchema):
    id: str  # "manual:<task_key>"
    name: str
    assignees: List[Assignee] = Field(default_factory=list)
    fields: List[ManualTaskField] = Field(default_factory=list)
    conditions: List[ManualTaskCondition] = Field(default_factory=list)
    gates: List[str] = Field(default_factory=list)


class PrivacyCenterFormRef(FidesSchema):
    id: str
    name: str
    url_path: str


class IdentityRoot(FidesSchema):
    id: Literal["identity-root"] = "identity-root"
    identity_types: List[str] = Field(default_factory=list)
    privacy_center_forms: List[PrivacyCenterFormRef] = Field(default_factory=list)


class PreviewEdge(FidesSchema):
    source: str
    target: str
    kind: Literal["depends_on", "gates"]
    dep_count: Optional[int] = None  # only set for "depends_on"


class TraversalPreview(FidesSchema):
    """Structured preview of a property-scoped DSR traversal — no property/cache metadata."""

    action_type: Literal["access", "erasure"]
    identity_root: IdentityRoot
    integrations: List[IntegrationNode] = Field(default_factory=list)
    manual_tasks: List[ManualTaskNode] = Field(default_factory=list)
    edges: List[PreviewEdge] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
