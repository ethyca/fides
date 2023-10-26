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
  preference: UserConsentPreference;
  privacy_notice_history_id?: string;
  privacy_preference_history_id: string;
  provided_identity_id?: string;
  created_at: string;
};
