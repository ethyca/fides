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
 * Request body for creating PrivacyPreferences.
 *
 *
 * "preferences" key reserved for saving preferences against a privacy notice.
 *
 * New *_preferences fields are used for saving preferences against various tcf components.
 */
export type PrivacyPreferencesRequest = {
  browser_identity: Identity;
  code?: string;
  preferences?: Array<ConsentOptionCreate>;
  purpose_preferences?: Array<TCFPurposeSave>;
  special_purpose_preferences?: Array<TCFSpecialPurposeSave>;
  vendor_preferences?: Array<TCFVendorSave>;
  feature_preferences?: Array<TCFFeatureSave>;
  special_feature_preferences?: Array<TCFSpecialFeatureSave>;
  system_preferences?: Array<TCFVendorSave>;
  policy_key?: string;
  privacy_experience_id?: string;
  user_geography?: string;
  method?: ConsentMethod;
};
