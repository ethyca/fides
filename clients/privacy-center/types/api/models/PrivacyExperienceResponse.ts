/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceConfigResponseNoNotices } from "./ExperienceConfigResponseNoNotices";
import type { ExperienceMeta } from "./ExperienceMeta";
import type { GPPApplicationConfigResponse } from "./GPPApplicationConfigResponse";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { PrivacyNoticeResponse } from "./PrivacyNoticeResponse";
import type { TCFFeatureRecord } from "./TCFFeatureRecord";
import type { TCFPurposeConsentRecord } from "./TCFPurposeConsentRecord";
import type { TCFPurposeLegitimateInterestsRecord } from "./TCFPurposeLegitimateInterestsRecord";
import type { TCFSpecialFeatureRecord } from "./TCFSpecialFeatureRecord";
import type { TCFSpecialPurposeRecord } from "./TCFSpecialPurposeRecord";
import type { TCFVendorConsentRecord } from "./TCFVendorConsentRecord";
import type { TCFVendorLegitimateInterestsRecord } from "./TCFVendorLegitimateInterestsRecord";
import type { TCFVendorRelationships } from "./TCFVendorRelationships";

/**
 * An API representation of a PrivacyExperience used for response payloads
 *
 * Notices are extracted from the shared Experience Config and placed at the top-level here
 * for backwards compatibility, and to reduce nesting due to notice translations.
 *
 * Additionally, the notices on the ExperienceConfig are further filtered.
 */
export type PrivacyExperienceResponse = {
  id: string;
  created_at: string;
  updated_at: string;
  region: PrivacyNoticeRegion;
  component?: ComponentType;
  gpp_settings?: GPPApplicationConfigResponse;
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
  /**
   * For backwards compatibility purposes, whether the Experience should show a banner.
   */
  show_banner?: boolean;
  /**
   * The Privacy Notices associated with this experience, if applicable
   */
  privacy_notices?: Array<PrivacyNoticeResponse>;
  /**
   * The Experience Config and its translations
   */
  experience_config?: ExperienceConfigResponseNoNotices;
  gvl?: any;
  meta?: ExperienceMeta;
};
