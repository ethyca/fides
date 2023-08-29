/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ComponentType } from "./ComponentType";
import type { ExperienceConfigResponse } from "./ExperienceConfigResponse";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { PrivacyNoticeResponseWithUserPreferences } from "./PrivacyNoticeResponseWithUserPreferences";
import type { TCFFeatureRecord } from "./TCFFeatureRecord";
import type { TCFPurposeRecord } from "./TCFPurposeRecord";
import type { TCFVendorRecord } from "./TCFVendorRecord";

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
  /**
   * For TCF Experiences, the TCF Purposes that appear on your Systems
   */
  tcf_purposes?: Array<TCFPurposeRecord>;
  /**
   * For TCF Experiences, the TCF Special Purposes that appear on your Systems
   */
  tcf_special_purposes?: Array<TCFPurposeRecord>;
  /**
   * For TCF Experiences, the TCF Vendors associated with your Systems
   */
  tcf_vendors?: Array<TCFVendorRecord>;
  /**
   * For TCF Experiences, the TCF Features that appear on your Systems
   */
  tcf_features?: Array<TCFFeatureRecord>;
  /**
   * For TCF Experiences, the TCF Special Features that appear on your Systems
   */
  tcf_special_features?: Array<TCFFeatureRecord>;
  /**
   * For TCF Experiences, Systems with TCF components that do not have an official vendor id (identified by system id)
   */
  tcf_systems?: Array<TCFVendorRecord>;
};
