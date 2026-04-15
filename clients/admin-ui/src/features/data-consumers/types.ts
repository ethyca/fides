export type ConsumerType =
  | "team"
  | "ai_agent"
  | "project"
  | "system"
  | "service_account";

export interface MockDataConsumer {
  id: string;
  name: string;
  identifier: string;
  type: ConsumerType;
  platform: string | null;
  purposes: string[];
  /** Dataset fides_keys this consumer is authorized to access. */
  datasets: string[];
  findingsCount: number;
  linkedSystem: string | null;
}

export interface ConsumerViolation {
  id: string;
  consumerId: string;
  dataset: string;
  table: string;
  accessedAt: string;
  description: string;
}

export interface ViolationDataset {
  name: string;
  tables: string[];
  queryCount: number;
  lastSeen: string;
}

export interface PolicyViolationGroup {
  purpose: string;
  totalQueries: number;
  datasets: ViolationDataset[];
}

export interface PolicyGap {
  dataset: string;
  tables: string[];
  queryCount: number;
  lastSeen: string;
  description: string;
}
