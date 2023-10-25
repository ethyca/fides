/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CurrentPrivacyPreferenceSchema } from "./CurrentPrivacyPreferenceSchema";
import type { TCMobileData } from "./TCMobileData";

/**
 * Response schema when saving privacy preferences
 */
export type SavePrivacyPreferencesResponse = {
  preferences?: Array<CurrentPrivacyPreferenceSchema>;
  purpose_consent_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  purpose_legitimate_interests_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  special_purpose_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  vendor_consent_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  vendor_legitimate_interests_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  feature_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  special_feature_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  system_consent_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  system_legitimate_interests_preferences?: Array<CurrentPrivacyPreferenceSchema>;
  fides_mobile_data?: TCMobileData;
};
