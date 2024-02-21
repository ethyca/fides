/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from './ConsentMechanism';
import type { Cookies } from './Cookies';
import type { EnforcementLevel } from './EnforcementLevel';
import type { GPPFieldMapping } from './GPPFieldMapping';
import type { NoticeTranslationResponse } from './NoticeTranslationResponse';
import type { PrivacyNoticeFramework } from './PrivacyNoticeFramework';
import type { PrivacyNoticeRegion } from './PrivacyNoticeRegion';
import type { UserConsentPreference } from './UserConsentPreference';

/**
 * Detailed Privacy Notice Response that also calculates which regions
 * are using the Notice
 */
export type PrivacyNoticeResponseWithRegions = {
  name?: string;
  notice_key?: string;
  internal_description?: string;
  consent_mechanism?: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level?: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  framework?: PrivacyNoticeFramework;
  default_preference?: UserConsentPreference;
  id: string;
  origin?: string;
  created_at: string;
  updated_at: string;
  cookies: Array<Cookies>;
  systems_applicable?: boolean;
  translations?: Array<NoticeTranslationResponse>;
  gpp_field_mapping?: Array<GPPFieldMapping>;
  /**
   * A property calculated by observing which Experiences have linked this Notice
   */
  configured_regions?: Array<PrivacyNoticeRegion>;
};

