/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyNoticeHistorySchema } from './PrivacyNoticeHistorySchema';

/**
 * Schema that surfaces the last version of a notice that was shown to a user
 */
export type LastServedNoticeSchema = {
  id: string;
  updated_at: string;
  privacy_notice_history: PrivacyNoticeHistorySchema;
  served_notice_history_id: string;
};

