/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { NoticeTranslationResponse } from "./NoticeTranslationResponse";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Another limited Privacy Notice Schema for the Detail view in the Admin UI
 * - limits number of fields returned for performance.
 *
 * "configured_regions" is a property calculated by observing which Experience Configs have linked this Notice
 */
export type PrivacyNoticeResponseWithRegions = {
  default_preference?: UserConsentPreference | null;
  id: string;
  name: string;
  disabled: boolean;
  created_at: string;
  updated_at: string;
  consent_mechanism: ConsentMechanism;
  notice_key: string;
  /**
   * A property calculated by observing which Experiences have linked this Notice
   */
  configured_regions_for_notice?: Array<PrivacyNoticeRegion>;
  data_uses: Array<string>;
  enforcement_level: EnforcementLevel;
  has_gpc_flag: boolean;
  translations?: Array<NoticeTranslationResponse>;
  children?: Array<PrivacyNoticeResponseWithRegions>;
};
