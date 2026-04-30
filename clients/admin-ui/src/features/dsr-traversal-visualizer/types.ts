import type { Node } from "@xyflow/react";

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
  system?: SystemRef;
  reachability: Reachability;
  action_status: ActionStatus;
  collection_count: { traversed: number; total: number };
  data_categories: string[];
  datasets: DatasetDetail[];
}

export interface ManualTaskNodeData extends Record<string, unknown> {
  id: string;
  name: string;
  assignees: { type: "user" | "team"; name: string }[];
  fields: { name: string; type: string }[];
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
