/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { Cookies } from "./Cookies";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { UserConsentPreference } from "./UserConsentPreference";
import type { NoticeTranslationResponse } from "./NoticeTranslationResponse";

export enum PrivacyNoticeFramework {
  GPP_US_NATIONAL = "gpp_us_national",
  GPP_US_STATE = "gpp_us_state",
}

export type GPPMechanismMapping = {
  field: string;
  not_available: string;
  opt_out: string;
  not_opt_out: string;
};

export type GPPFieldMapping = {
  region: string;
  notice?: Array<string>;
  mechanism?: Array<GPPMechanismMapping>;
};

/**
 * If retrieving notices for a given user, also return the default preferences for that notice
 * and any saved preferences.
 */
export type PrivacyNoticeResponseWithUserPreferences = {
  translations: Array<NoticeTranslationResponse>;
  name?: string;
  notice_key?: string;
  internal_description?: string;
  origin?: string;
  consent_mechanism?: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level?: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  framework?: PrivacyNoticeFramework;
  gpp_field_mapping?: Array<GPPFieldMapping>;
  id: string;
  created_at: string;
  updated_at: string;
  cookies: Array<Cookies>;
  default_preference?: UserConsentPreference;
  systems_applicable?: boolean;
};
