export type PrivacyRequestStatus =
  | "approved"
  | "complete"
  | "denied"
  | "error"
  | "in_processing"
  | "paused"
  | "canceled"
  | "pending";

export enum ActionType {
  ACCESS = "access",
  ERASURE = "erasure",
}

export interface DenyPrivacyRequest {
  id: string;
  reason: string;
}

interface FieldsAffected {
  path: string;
  field_name: string;
  data_categories: string[];
}

export enum ExecutionLogStatus {
  IN_PROCESSING = "in_processing",
  PENDING = "pending",
  COMPLETE = "complete",
  ERROR = "error",
  PAUSED = "paused",
  RETRYING = "retrying",
  SKIPPED = "skipped",
}

export interface ExecutionLog {
  collection_name: string;
  fields_affected: FieldsAffected[];
  message: string;
  action_type: string;
  status: ExecutionLogStatus;
  updated_at: string;
}

export interface Rule {
  name: string;
  key: string;
  action_type: ActionType;
}

export type PrivacyRequestResults = Record<string, ExecutionLog[]>;

export interface PrivacyRequest {
  status: PrivacyRequestStatus;
  results?: PrivacyRequestResults;
  identity: {
    email?: string;
    phone_number?: string;
  };
  policy: {
    name: string;
    key: string;
    rules: Rule[];
  };
  reviewer: {
    id: string;
    username: string;
  };
  created_at: string;
  reviewed_by: string;
  id: string;
}

export interface PrivacyRequestResponse {
  items: PrivacyRequest[];
  total: number;
}

export interface PrivacyRequestParams {
  status?: PrivacyRequestStatus[];
  id: string;
  from: string;
  to: string;
  page: number;
  size: number;
  verbose?: boolean;
}
