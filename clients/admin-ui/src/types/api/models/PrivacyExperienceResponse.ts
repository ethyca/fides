/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceConfigResponse } from "./ExperienceConfigResponse";
import type { ExperienceMeta } from "./ExperienceMeta";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { PrivacyNoticeResponseWithUserPreferences } from "./PrivacyNoticeResponseWithUserPreferences";
import type { TCFConsentVendorRecord } from "./TCFConsentVendorRecord";
import type { TCFFeatureRecord } from "./TCFFeatureRecord";
import type { TCFLegitimateInterestsVendorRecord } from "./TCFLegitimateInterestsVendorRecord";
import type { TCFPurposeConsentRecord } from "./TCFPurposeConsentRecord";
import type { TCFPurposeLegitimateInterestsRecord } from "./TCFPurposeLegitimateInterestsRecord";
import type { TCFSpecialFeatureRecord } from "./TCFSpecialFeatureRecord";
import type { TCFSpecialPurposeRecord } from "./TCFSpecialPurposeRecord";
import type { TCFVendorRelationships } from "./TCFVendorRelationships";

/**
 * An API representation of a PrivacyExperience used for response payloads
 */
export type PrivacyExperienceResponse = {
  region: PrivacyNoticeRegion;
  component?: ComponentType;
  /**
   * The Experience copy or language
   */
  experience_config?: ExperienceConfigResponse;
  id: string;
  tcf_consent_purposes?: Array<TCFPurposeConsentRecord>;
  tcf_legitimate_interests_purposes?: Array<TCFPurposeLegitimateInterestsRecord>;
  tcf_special_purposes?: Array<TCFSpecialPurposeRecord>;
  tcf_features?: Array<TCFFeatureRecord>;
  tcf_special_features?: Array<TCFSpecialFeatureRecord>;
  tcf_consent_vendors?: Array<TCFConsentVendorRecord>;
  tcf_legitimate_interests_vendors?: Array<TCFLegitimateInterestsVendorRecord>;
  tcf_vendor_relationships?: Array<TCFVendorRelationships>;
  tcf_consent_systems?: Array<TCFConsentVendorRecord>;
  tcf_legitimate_interests_systems?: Array<TCFLegitimateInterestsVendorRecord>;
  tcf_system_relationships?: Array<TCFVendorRelationships>;
  created_at: string;
  updated_at: string;
  /**
   * Whether the experience should show a banner
   */
  show_banner?: boolean;
  /**
   * The Privacy Notices associated with this experience, if applicable
   */
  privacy_notices?: Array<PrivacyNoticeResponseWithUserPreferences>;
  gvl?: any;
  meta?: ExperienceMeta;
};
