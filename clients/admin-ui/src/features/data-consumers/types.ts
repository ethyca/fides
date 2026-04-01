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
  violationCount: number;
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
