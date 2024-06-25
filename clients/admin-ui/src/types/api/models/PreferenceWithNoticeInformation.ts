/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Preference with additional notice information.
 */
export type PreferenceWithNoticeInformation = {
  privacy_notice_history_id: string;
  preference: UserConsentPreference;
  notice_key: string;
  notice_id: string;
  version: number;
};
