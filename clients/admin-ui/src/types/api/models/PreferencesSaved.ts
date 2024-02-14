/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentOptionCreate } from './ConsentOptionCreate';
import type { TCFFeatureSave } from './TCFFeatureSave';
import type { TCFPurposeSave } from './TCFPurposeSave';
import type { TCFSpecialFeatureSave } from './TCFSpecialFeatureSave';
import type { TCFSpecialPurposeSave } from './TCFSpecialPurposeSave';
import type { TCFVendorSave } from './TCFVendorSave';

/**
 * All preference types against which consent can be saved - including both Privacy Notices and TCF attributes
 *
 * # NOTE: The "preferences" key is for saving preferences against Privacy Notices only, not TCF preferences.
 */
export type PreferencesSaved = {
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
};

