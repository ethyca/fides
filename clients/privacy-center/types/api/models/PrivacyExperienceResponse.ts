/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceConfigResponse } from "./ExperienceConfigResponse";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { PrivacyNoticeResponseWithUserPreferences } from "./PrivacyNoticeResponseWithUserPreferences";
import type { TCFFeatureRecord } from "./TCFFeatureRecord";
import type { TCFPurposeConsentRecord } from "./TCFPurposeConsentRecord";
import type { TCFPurposeLegitimateInterestsRecord } from "./TCFPurposeLegitimateInterestsRecord";
import type { TCFSpecialFeatureRecord } from "./TCFSpecialFeatureRecord";
import type { TCFSpecialPurposeRecord } from "./TCFSpecialPurposeRecord";
import type { TCFVendorConsentRecord } from "./TCFVendorConsentRecord";
import type { TCFVendorLegitimateInterestsRecord } from "./TCFVendorLegitimateInterestsRecord";
import type { TCFVendorRelationships } from "./TCFVendorRelationships";
import { ExperienceMeta } from "fides-js";

/**
 * An API representation of a PrivacyExperience used for response payloads
 */
export type PrivacyExperienceResponse = {
  // TODO- update with new BE resp body
  region: PrivacyNoticeRegion;
  disabled?: boolean;
  component?: ComponentType; // deprecated- don't use
  /**
   * The Experience copy or language
   */
  experience_config?: ExperienceConfigResponse;
  id: string;
  tcf_purpose_consents?: Array<TCFPurposeConsentRecord>;
  tcf_purpose_legitimate_interests?: Array<TCFPurposeLegitimateInterestsRecord>;
  tcf_special_purposes?: Array<TCFSpecialPurposeRecord>;
  tcf_features?: Array<TCFFeatureRecord>;
  tcf_special_features?: Array<TCFSpecialFeatureRecord>;
  tcf_vendor_consents?: Array<TCFVendorConsentRecord>;
  tcf_vendor_legitimate_interests?: Array<TCFVendorLegitimateInterestsRecord>;
  tcf_vendor_relationships?: Array<TCFVendorRelationships>;
  tcf_system_consents?: Array<TCFVendorConsentRecord>;
  tcf_system_legitimate_interests?: Array<TCFVendorLegitimateInterestsRecord>;
  tcf_system_relationships?: Array<TCFVendorRelationships>;
  created_at: string;
  updated_at: string;
  /**
   * The Privacy Notices associated with this experience, if applicable
   */
  privacy_notices?: Array<PrivacyNoticeResponseWithUserPreferences>;
  gvl?: any;
  meta?: ExperienceMeta;
};
