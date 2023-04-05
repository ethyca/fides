/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation of a PrivacyNotice used for response payloads
 */
export type PrivacyNoticeResponse = {
  name?: string;
  description?: string;
  origin?: string;
  regions?: Array<PrivacyNoticeRegion>;
  consent_mechanism?: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level?: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  displayed_in_privacy_center?: boolean;
  displayed_in_privacy_modal?: boolean;
  displayed_in_banner?: boolean;
  id: string;
  created_at: string;
  updated_at: string;
  version: number;
};
