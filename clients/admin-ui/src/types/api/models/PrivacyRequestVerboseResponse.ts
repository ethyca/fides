/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CheckpointActionRequiredDetails } from "./CheckpointActionRequiredDetails";
import type { ExecutionAndAuditLogResponse } from "./ExecutionAndAuditLogResponse";
import type { PolicyResponse } from "./PolicyResponse";
import type { PrivacyRequestReviewer } from "./PrivacyRequestReviewer";
import type { PrivacyRequestSource } from "./PrivacyRequestSource";
import type { PrivacyRequestStatus } from "./PrivacyRequestStatus";

/**
 * The schema for the more detailed PrivacyRequest response containing both
 * detailed execution logs and audit logs.
 */
export type PrivacyRequestVerboseResponse = {
  id: string;
  created_at?: string;
  started_processing_at?: string;
  reviewed_at?: string;
  reviewed_by?: string;
  reviewer?: PrivacyRequestReviewer;
  finished_processing_at?: string;
  identity_verified_at?: string;
  paused_at?: string;
  status: PrivacyRequestStatus;
  external_id?: string;
  identity?: Record<string, string>;
  custom_privacy_request_fields?: any;
  policy: PolicyResponse;
  action_required_details?: CheckpointActionRequiredDetails;
  resume_endpoint?: string;
  days_left?: number;
  custom_privacy_request_fields_approved_by?: string;
  custom_privacy_request_fields_approved_at?: string;
  source?: PrivacyRequestSource;
  results: Record<string, Array<ExecutionAndAuditLogResponse>>;
};
