/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { Cookies } from "./Cookies";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { GPPFieldMapping } from "./GPPFieldMapping";
import type { PrivacyNoticeFramework } from "./PrivacyNoticeFramework";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * An API representation of a PrivacyNotice used for response payloads
 */
export type PrivacyNoticeResponse = {
  name?: string;
  notice_key?: string;
  description?: string;
  internal_description?: string;
  origin?: string;
  regions?: Array<PrivacyNoticeRegion>;
  consent_mechanism?: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level?: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  displayed_in_privacy_center?: boolean;
  displayed_in_overlay?: boolean;
  displayed_in_api?: boolean;
  framework?: PrivacyNoticeFramework;
  gpp_field_mapping?: Array<GPPFieldMapping>;
  id: string;
  default_preference?: UserConsentPreference;
  created_at: string;
  updated_at: string;
  version: number;
  privacy_notice_history_id: string;
  cookies: Array<Cookies>;
  systems_applicable?: boolean;
};
