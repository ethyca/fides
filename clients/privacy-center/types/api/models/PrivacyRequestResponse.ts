/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CheckpointActionRequiredDetails } from "./CheckpointActionRequiredDetails";
import type { PolicyResponse } from "./PolicyResponse";
import type { PrivacyRequestReviewer } from "./PrivacyRequestReviewer";
import type { PrivacyRequestSource } from "./PrivacyRequestSource";
import type { PrivacyRequestStatus } from "./PrivacyRequestStatus";

/**
 * Schema to check the status of a PrivacyRequest
 */
export type PrivacyRequestResponse = {
  id: string;
  created_at?: string | null;
  started_processing_at?: string | null;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  reviewer?: PrivacyRequestReviewer | null;
  finished_processing_at?: string | null;
  identity_verified_at?: string | null;
  paused_at?: string | null;
  status: PrivacyRequestStatus;
  external_id?: string | null;
  identity?: Record<string, string | null> | null;
  custom_privacy_request_fields?: null;
  policy: PolicyResponse;
  action_required_details?: CheckpointActionRequiredDetails | null;
  resume_endpoint?: string | null;
  days_left?: number | null;
  custom_privacy_request_fields_approved_by?: string | null;
  custom_privacy_request_fields_approved_at?: string | null;
  source?: PrivacyRequestSource | null;
};
