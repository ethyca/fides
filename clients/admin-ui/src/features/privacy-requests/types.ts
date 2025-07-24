import {
  ActionType,
  AttachmentResponse,
  DrpAction,
  PrivacyRequestStatus,
} from "~/types/api";

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
  AWAITING_PROCESSING = "awaiting_processing",
  RETRYING = "retrying",
  SKIPPED = "skipped",
}

export const ExecutionLogStatusLabels: Record<ExecutionLogStatus, string> = {
  [ExecutionLogStatus.IN_PROCESSING]: "In processing",
  [ExecutionLogStatus.PENDING]: "Pending",
  [ExecutionLogStatus.COMPLETE]: "Complete",
  [ExecutionLogStatus.ERROR]: "Error",
  [ExecutionLogStatus.PAUSED]: "Paused",
  [ExecutionLogStatus.AWAITING_PROCESSING]: "Awaiting input",
  [ExecutionLogStatus.RETRYING]: "Retrying",
  [ExecutionLogStatus.SKIPPED]: "Skipped",
};

export const ExecutionLogStatusColors: Record<
  ExecutionLogStatus,
  string | undefined
> = {
  [ExecutionLogStatus.ERROR]: "error",
  [ExecutionLogStatus.SKIPPED]: "warning",
  [ExecutionLogStatus.AWAITING_PROCESSING]: "minos",
  [ExecutionLogStatus.IN_PROCESSING]: undefined,
  [ExecutionLogStatus.PENDING]: undefined,
  [ExecutionLogStatus.COMPLETE]: undefined,
  [ExecutionLogStatus.PAUSED]: undefined,
  [ExecutionLogStatus.RETRYING]: undefined,
};

export interface ExecutionLog {
  collection_name: string | null;
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

export interface MessagingConfigResponse {
  storage: {
    active_default_storage_type: string;
  };
}

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

export interface S3SecretsDetails {
  aws_access_key_id: string;
  aws_secret_access_key: string;
}

export interface GCSSecretsDetails {
  type: string;
  project_id: string;
  private_key_id: string;
  private_key: string;
  client_email: string;
  client_id: string;
  auth_uri: string;
  token_uri: string;
  auth_provider_x509_cert_url: string;
  client_x509_cert_url: string;
  universe_domain: string;
}

export interface ConfigStorageSecretsDetailsRequest {
  type?: string;
  details?: S3SecretsDetails | GCSSecretsDetails;
}

export interface ConfigMessagingRequest {
  type: string;
}

export interface ConfigMessagingDetailsRequest {
  service_type: string;
  details?: {
    is_eu_domain?: string;
    domain?: string;
    twilio_email_from?: string;
  };
}

export interface ConfigMessagingSecretsRequest {
  service_type?: string;
  details?: {
    twilio_api_key?: string;
    mailgun_api_key?: string;
    twilio_account_sid?: string;
    twilio_auth_token?: string;
    twilio_messaging_service_sid?: string;
    twilio_sender_phone_number?: string;
  };
}

export enum ActivityTimelineItemTypeEnum {
  REQUEST_UPDATE = "Request update",
  INTERNAL_COMMENT = "Internal comment",
  MANUAL_TASK = "Manual task",
}

export const TimelineItemColorMap: Record<
  ActivityTimelineItemTypeEnum,
  string
> = {
  [ActivityTimelineItemTypeEnum.REQUEST_UPDATE]: "sandstone",
  [ActivityTimelineItemTypeEnum.INTERNAL_COMMENT]: "marble",
  [ActivityTimelineItemTypeEnum.MANUAL_TASK]: "nectar",
};

export interface ActivityTimelineItem {
  author: string;
  title?: string;
  date: Date;
  type: ActivityTimelineItemTypeEnum;
  showViewLog: boolean;
  onClick?: () => void;
  description?: string;
  isError: boolean;
  isSkipped: boolean;
  isAwaitingInput: boolean;
  id: string;
  attachments?: AttachmentResponse[];
}
