/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { ConsentMethod } from "./ConsentMethod";
import type { ExecutionLogStatus } from "./ExecutionLogStatus";
import type { PrivacyRequestStatus } from "./PrivacyRequestStatus";
import type { RequestOrigin } from "./RequestOrigin";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for consent reporting - largely a join of PrivacyPreferenceHistory and PrivacyRequest
 */
export type ConsentReportingSchema = {
  purpose_consent?: number;
  purpose_legitimate_interests?: number;
  special_purpose?: number;
  vendor_consent?: string;
  vendor_legitimate_interests?: string;
  feature?: number;
  special_feature?: number;
  system_consent?: string;
  system_legitimate_interests?: string;
  id: string;
  privacy_request_id?: string;
  email?: string;
  phone_number?: string;
  fides_user_device_id?: string;
  secondary_user_ids?: any;
  request_timestamp: string;
  request_origin?: RequestOrigin;
  request_status?: PrivacyRequestStatus;
  request_type: ActionType;
  approver_id?: string;
  privacy_notice_history_id?: string;
  preference: UserConsentPreference;
  user_geography?: string;
  relevant_systems?: Array<string>;
  affected_system_status: Record<string, ExecutionLogStatus>;
  url_recorded?: string;
  user_agent?: string;
  experience_config_history_id?: string;
  privacy_experience_id?: string;
  truncated_ip_address?: string;
  method?: ConsentMethod;
  served_notice_history_id?: string;
  tcf_version?: string;
};
