/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { fides__api__schemas__privacy_notice__GPPUSApproach } from "./fides__api__schemas__privacy_notice__GPPUSApproach";
import type { GPPFieldMapping } from "./GPPFieldMapping";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation of a PrivacyNotice that includes an `id` field.
 * Used to help model API responses and update payloads
 */
export type PrivacyNoticeWithId = {
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
  gpp_us_approach?: fides__api__schemas__privacy_notice__GPPUSApproach;
  gpp_field_mapping?: Array<GPPFieldMapping>;
  id: string;
};
