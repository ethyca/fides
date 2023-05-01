/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema to represent the latest saved preference for a given privacy notice
 * Note that we return the privacy notice *history* record here though which has the
 * contents of the notice the user consented to at the time.
 */
export type CurrentPrivacyPreferenceReportingSchema = {
  id: string;
  preference: UserConsentPreference;
  privacy_notice_history_id: string;
  privacy_preference_history_id: string;
  provided_identity_id?: string;
  created_at: string;
};
