import type { Node } from "@xyflow/react";

import {
  ActionStatus,
  type Assignee,
  type CollectionDetail as GeneratedCollectionDetail,
  type DatasetDetail as GeneratedDatasetDetail,
  type FieldDetail as GeneratedFieldDetail,
  type IdentityRoot,
  type IntegrationNode,
  type ManualTaskCondition,
  type ManualTaskField as ManualTaskFieldDetail,
  type ManualTaskNode,
  type PreviewEdge,
  type PrivacyCenterFormRef,
  Reachability,
  type SystemRef,
  type TraversalPreviewResponse as GeneratedTraversalPreviewResponse,
} from "~/types/api";

// Re-export generated types so callers can keep importing from this feature
// without reaching into ~/types/api/models.
export { ActionStatus, Reachability };
export type {
  Assignee,
  ManualTaskCondition,
  ManualTaskFieldDetail,
  PreviewEdge,
  PrivacyCenterFormRef,
  SystemRef,
};

// Tighten optional list fields that the backend always emits via Pydantic
// `default_factory=list`. OpenAPI marks them optional because of the default,
// but they're guaranteed at runtime.
export interface FieldDetail extends Omit<
  GeneratedFieldDetail,
  "data_categories"
> {
  data_categories: string[];
}

export interface CollectionDetail extends Omit<
  GeneratedCollectionDetail,
  "fields"
> {
  fields: FieldDetail[];
}

export interface DatasetDetail extends Omit<
  GeneratedDatasetDetail,
  "collections"
> {
  collections: CollectionDetail[];
}

export enum LaneId {
  IDENTITY = "identity",
  REACH = "reach",
  GATED = "gated",
  SKIPPED = "skipped",
}

// Narrowed locally: the traversal preview only supports access + erasure.
// The generated ActionType also includes CONSENT and UPDATE, which the
// visualizer's action toggle does not expose.
export enum ActionType {
  ACCESS = "access",
  ERASURE = "erasure",
}

// React Flow's `Node<T>` requires the data type to extend
// `Record<string, unknown>`, so each *Data interface wraps the generated
// schema with that mix-in. The wrapper also tightens list fields that the
// backend always emits (Pydantic `default_factory=list`) but OpenAPI marks
// optional. `stage_via` is an admin-ui-only derived field (plain-English
// upstream system name for stage 2+ cards) and isn't on the backend payload.
export interface IntegrationNodeData
  extends
    Omit<IntegrationNode, "data_categories" | "datasets">,
    Record<string, unknown> {
  data_categories: string[];
  datasets: DatasetDetail[];
  stage_via?: string | null;
}

export interface ManualTaskNodeData
  extends
    Omit<ManualTaskNode, "assignees" | "fields" | "conditions" | "gates">,
    Record<string, unknown> {
  assignees: Assignee[];
  fields: ManualTaskFieldDetail[];
  conditions: ManualTaskCondition[];
  gates: string[];
}

export interface IdentityRootData
  extends
    Omit<IdentityRoot, "id" | "identity_types" | "privacy_center_forms">,
    Record<string, unknown> {
  id: "identity-root";
  identity_types: string[];
  privacy_center_forms: PrivacyCenterFormRef[];
}

export interface TraversalPreviewResponse extends Omit<
  GeneratedTraversalPreviewResponse,
  "action_type" | "identity_root" | "integrations" | "manual_tasks" | "edges"
> {
  action_type: ActionType;
  identity_root: IdentityRootData;
  integrations: IntegrationNodeData[];
  manual_tasks: ManualTaskNodeData[];
  edges: PreviewEdge[];
}

export type AppNode =
  | Node<IdentityRootData, "identityRoot">
  | Node<IntegrationNodeData, "integration">
  | Node<ManualTaskNodeData, "manualTask">;

export interface StageBlock {
  /** 1-based index — Stage 1, Stage 2, ... */
  index: number;
  /** Plain-English label, e.g. "Stage 1 · From identity". */
  label: string;
  /** Plain-English tooltip. */
  tooltip: string;
  /** Cards in this stage, in render order. */
  nodeIds: string[];
  /** Lane-local x where the stage's left edge sits (after LANE_PADDING_X). */
  xStart: number;
  /** Lane-local x where the stage's right edge sits. */
  xEnd: number;
  /** Stage width — equals NODE_WIDTH + (columns - 1) * COL_WIDTH. */
  width: number;
  /** Lane-local y of the stage sub-header (sits below the lane header). */
  headerY: number;
  /** Lane-local y of the first card row (below the stage sub-header). */
  gridY: number;
  /** Column count promoted for this stage (1, 2, or 3). */
  columns: number;
}

export interface LaneBounds {
  id: LaneId;
  /** Pixel X of the lane's left edge in the canvas coord system. */
  x: number;
  y: number;
  width: number;
  height: number;
  /** Card count, used for the header chip. */
  cardCount: number;
  /** Whether the lane is currently collapsed (header-only). */
  collapsed: boolean;
  /** True if the lane has no cards and is hidden entirely. */
  hidden: boolean;
  /** Plain-English label and tooltip. */
  label: string;
  tooltip: string;
  /** Stage blocks — only populated for the reach lane. */
  stages?: StageBlock[];
  /** True for the not-touched lane — drawn separated from the flow rail. */
  outOfFlow?: boolean;
}

export interface LaneLayoutResult {
  /** Per-node positions, keyed by node id. */
  positions: Record<string, { x: number; y: number }>;
  /** Lane bounds in render order (left to right). */
  lanes: LaneBounds[];
  /** Total canvas size for fit/sizing calculations. */
  canvas: { width: number; height: number };
}

export type LaneCollapseMap = Record<LaneId, boolean>;
