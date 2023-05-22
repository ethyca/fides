/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * If retrieving notices for a given user, also return the default preferences for that notice
 * and any saved preferences.
 */
export type PrivacyNoticeResponseWithUserPreferences = {
  name?: string;
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
  id: string;
  created_at: string;
  updated_at: string;
  version: number;
  privacy_notice_history_id: string;
  default_preference: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
};
