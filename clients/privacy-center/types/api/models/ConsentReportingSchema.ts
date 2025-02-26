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
  id: string;
  privacy_request_id?: string | null;
  email?: string | null;
  phone_number?: string | null;
  external_id?: string | null;
  fides_user_device_id?: string | null;
  secondary_user_ids?: null;
  request_timestamp: string;
  request_origin?: RequestOrigin | null;
  request_status?: PrivacyRequestStatus | null;
  request_type: ActionType;
  approver_id?: string | null;
  privacy_notice_history_id?: string | null;
  preference?: UserConsentPreference | null;
  user_geography?: string | null;
  affected_system_status: Record<string, ExecutionLogStatus>;
  url_recorded?: string | null;
  user_agent?: string | null;
  experience_config_history_id?: string | null;
  truncated_ip_address?: string | null;
  method?: ConsentMethod | null;
  served_notice_history_id?: string | null;
  notice_name?: string | null;
  tcf_preferences?: null;
  property_id?: string | null;
};
