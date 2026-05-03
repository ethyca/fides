import type { Node } from "@xyflow/react";

import { LaneId } from "./constants";

export type ActionType = "access" | "erasure";
export type Reachability =
  | "reachable"
  | "unreachable"
  | "requires_manual_identity";
export type ActionStatus = "active" | "skipped";

export interface FieldDetail {
  name: string;
  data_categories: string[];
  is_identity: boolean;
}

export interface CollectionDetail {
  name: string;
  skipped: boolean;
  fields: FieldDetail[];
}

export interface DatasetDetail {
  fides_key: string;
  collections: CollectionDetail[];
}

export interface SystemRef {
  fides_key: string;
  name: string;
  data_use?: string;
}

export interface IntegrationNodeData extends Record<string, unknown> {
  id: string;
  connection_key: string;
  connector_type: string;
  saas_type?: string | null;
  system?: SystemRef;
  reachability: Reachability;
  action_status: ActionStatus;
  collection_count: { traversed: number; total: number };
  data_categories: string[];
  datasets: DatasetDetail[];
  /** Optional plain-English upstream system name, populated for stage 2+ cards. */
  stage_via?: string | null;
}

export interface ManualTaskFieldDetail {
  name: string;
  type: string;
  label?: string | null;
  help_text?: string | null;
  required?: boolean;
}

export interface ManualTaskNodeData extends Record<string, unknown> {
  id: string;
  name: string;
  assignees: { type: "user" | "team"; name: string }[];
  fields: ManualTaskFieldDetail[];
  conditions: { summary: string; expression: string }[];
  gates: string[];
}

export interface PrivacyCenterFormRef {
  id: string;
  name: string;
  url_path: string;
}

export interface IdentityRootData extends Record<string, unknown> {
  id: "identity-root";
  identity_types: string[];
  privacy_center_forms: PrivacyCenterFormRef[];
}

export interface PreviewEdge {
  source: string;
  target: string;
  kind: "depends_on" | "gates";
  dep_count?: number;
}

export interface TraversalPreviewResponse {
  property: { id: string; name: string };
  action_type: ActionType;
  computed_at: string;
  cache_hit: boolean;
  identity_root: IdentityRootData;
  integrations: IntegrationNodeData[];
  manual_tasks: ManualTaskNodeData[];
  edges: PreviewEdge[];
  warnings: string[];
}

export type AppNode =
  | Node<IdentityRootData, "identityRoot">
  | Node<IntegrationNodeData, "integration">
  | Node<ManualTaskNodeData, "manualTask">;

export interface StageBlock {
  /** 1-based index — Stage 1, Stage 2, ... */
  index: number;
  /** Plain-English label, e.g. "First — from identity directly". */
  label: string;
  /** Plain-English tooltip. */
  tooltip: string;
  /** Cards in this stage, in render order. */
  nodeIds: string[];
  /** Y where this block starts inside its lane. */
  yStart: number;
  /** Y where this block ends. */
  yEnd: number;
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
