/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PrivacyNoticeHistorySchema } from "./PrivacyNoticeHistorySchema";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema to represent the latest saved preference for a given privacy notice
 * Note that we return the privacy notice *history* record here though which has the
 * contents of the notice the user consented to at the time.
 */
export type CurrentPrivacyPreferenceSchema = {
  id: string;
  preference: UserConsentPreference;
  privacy_notice_history: PrivacyNoticeHistorySchema;
  privacy_preference_history_id: string;
};
