/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExperienceMinimalMeta } from "./ExperienceMinimalMeta";
import type { MinimalTCFExperienceConfig } from "./MinimalTCFExperienceConfig";
import type { PrivacyExperienceGPPSettings } from "./PrivacyExperienceGPPSettings";
import type { PrivacyNoticeResponse } from "./PrivacyNoticeResponse";

/**
 * Minimal TCF Banner Privacy Experience response that has the details to show the most minimal
 * TCF banner possible and the details to make a follow up request to save that notices were served.
 */
export type TCFBannerExperienceMinimalResponse = {
  /**
   * Available translations for this experience
   */
  available_locales?: Array<string> | null;
  /**
   * A minimal version of the experience config with the default translation only
   */
  experience_config?: MinimalTCFExperienceConfig | null;
  /**
   * The Privacy Notices associated with this experience, if applicable
   */
  privacy_notices?: Array<PrivacyNoticeResponse> | null;
  gpp_settings?: PrivacyExperienceGPPSettings | null;
  /**
   * Privacy Experience ID
   */
  id: string;
  gvl?: null;
  meta?: ExperienceMinimalMeta | null;
  /**
   * Helps FE detect that this is a minimal TCF response
   */
  minimal_tcf?: boolean | null;
  /**
   * TCF Purpose names for banner display
   */
  tcf_purpose_names: Array<string>;
  /**
   * TCF Special Feature names for banner display
   */
  tcf_special_feature_names: Array<string>;
  /**
   * Feature IDs
   */
  tcf_feature_ids: Array<number>;
  /**
   * Purpose IDs used with legal basis of consent
   */
  tcf_purpose_consent_ids: Array<number>;
  /**
   * Purpose IDs used with legal basis of legitimate interests
   */
  tcf_purpose_legitimate_interest_ids: Array<number>;
  /**
   * Special feature IDs
   */
  tcf_special_feature_ids: Array<number>;
  /**
   * Special purpose IDs
   */
  tcf_special_purpose_ids: Array<number>;
  /**
   * Fides system IDs using data with legal basis of legitimate interests
   */
  tcf_system_consent_ids: Array<string>;
  /**
   * Fides System IDs using data with legal basis of legitimate interests
   */
  tcf_system_legitimate_interest_ids: Array<string>;
  /**
   * Vendor IDs using data with legal basis of consent
   */
  tcf_vendor_consent_ids: Array<string>;
  /**
   * Vendor IDs using data with legal basis of legitimate interests
   */
  tcf_vendor_legitimate_interest_ids: Array<string>;
  /**
   * The total number of Vendors and Fides systems displayed in the TCF Experience
   */
  vendor_count?: number | null;
};
