/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyNoticeHistorySchema } from "./PrivacyNoticeHistorySchema";

/**
 * Schema that surfaces the the last time a consent item that was shown to a user
 */
export type LastServedConsentSchema = {
  purpose?: number;
  special_purpose?: number;
  vendor?: string;
  feature?: number;
  special_feature?: number;
  system?: string;
  id: string;
  updated_at: string;
  served_notice_history_id: string;
  privacy_notice_history?: PrivacyNoticeHistorySchema;
};
