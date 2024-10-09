import { ActionType, DrpAction, PrivacyRequestStatus } from "~/types/api";

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

export type GetUploadedManualWebhookDataRequest = {
  connection_key: string;
  privacy_request_id: string;
};

export interface Rule {
  name: string;
  key: string;
  action_type: ActionType;
}

export type PatchUploadManualWebhookDataRequest = {
  body: object;
  connection_key: string;
  privacy_request_id: string;
};

export type PrivacyRequestResults = Record<string, ExecutionLog[]>;

export interface PrivacyRequestEntity {
  status: PrivacyRequestStatus;
  results?: PrivacyRequestResults;
  identity: {
    [key: string]: { label: string; value: any };
  };
  identity_verified_at?: string;
  custom_privacy_request_fields?: {
    [key: string]: { label: string; value: any };
  };
  custom_privacy_request_fields_approved_by?: string;
  custom_privacy_request_fields_approved_at?: string;
  policy: {
    name: string;
    key: string;
    rules: Rule[];
    drp_action?: DrpAction;
    execution_timeframe?: number;
  };
  reviewer: {
    id: string;
    username: string;
  };
  created_at: string;
  reviewed_by: string;
  id: string;
  days_left?: number;
  source?: string;
}

export interface PrivacyRequestResponse {
  items: PrivacyRequestEntity[];
  total: number;
  page?: number;
  pages?: number;
  size?: number;
}

export interface PrivacyRequestParams {
  status?: PrivacyRequestStatus[];
  action_type?: ActionType[];
  fuzzy_search_str?: string;
  id: string;
  from: string;
  to: string;
  page: number;
  size: number;
  verbose?: boolean;
  sort_field?: string;
  sort_direction?: string;
}

export type RetryRequests = {
  checkAll: boolean;
  errorRequests: string[];
};

export interface StorageConfigResponse {
  notifications: {
    notification_service_type: string;
    send_request_completion_notification: boolean;
    send_request_receipt_notification: boolean;
    send_request_review_notification: boolean;
  };
  execution: {
    subject_identity_verification_required: true;
  };
}

export interface ConfigStorageDetailsRequest {
  type: string;
  auth_method?: string;
  bucket?: string;
  details?: {
    auth_method?: string;
    bucket?: string;
  };
  key?: string;
  format?: string;
}

export interface ConfigStorageSecretsDetailsRequest {
  type?: string;
  details?: {
    aws_access_key_id: string;
    aws_secret_access_key: string;
  };
}
