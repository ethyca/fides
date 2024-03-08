/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMethod } from "./ConsentMethod";
import type { ConsentOptionCreate } from "./ConsentOptionCreate";
import type { Identity } from "./Identity";
import type { TCFFeatureSave } from "./TCFFeatureSave";
import type { TCFPurposeSave } from "./TCFPurposeSave";
import type { TCFSpecialFeatureSave } from "./TCFSpecialFeatureSave";
import type { TCFSpecialPurposeSave } from "./TCFSpecialPurposeSave";
import type { TCFVendorSave } from "./TCFVendorSave";

/**
 * Request body for saving PrivacyPreferences.
 *
 * "preferences" key reserved for saving preferences against a privacy notice.
 *
 * New *_preferences fields are used for saving preferences against various tcf components.
 */
export type PrivacyPreferencesRequest = {
  purpose_consent_preferences?: Array<TCFPurposeSave>;
  purpose_legitimate_interests_preferences?: Array<TCFPurposeSave>;
  vendor_consent_preferences?: Array<TCFVendorSave>;
  vendor_legitimate_interests_preferences?: Array<TCFVendorSave>;
  special_feature_preferences?: Array<TCFSpecialFeatureSave>;
  special_purpose_preferences?: Array<TCFSpecialPurposeSave>;
  feature_preferences?: Array<TCFFeatureSave>;
  system_consent_preferences?: Array<TCFVendorSave>;
  system_legitimate_interests_preferences?: Array<TCFVendorSave>;
  preferences?: Array<ConsentOptionCreate>;
  browser_identity: Identity;
  code?: string;
  /**
   * If supplied, TC strings and AC strings are decoded and preferences saved for purpose_consent, purpose_legitimate_interests, vendor_consent, vendor_legitimate_interests, and special_features
   */
  fides_string?: string;
  policy_key?: string;
  /**
   * @deprecated has no effect; use privacy_experience_config_history_id instead!
   */
  privacy_experience_id?: string;
  privacy_experience_config_history_id?: string;
  user_geography?: string;
  method?: ConsentMethod;
  served_notice_history_id?: string;
};
