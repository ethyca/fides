/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * An API representation of a PrivacyNoticeHistory used for response payloads
 */
export type PrivacyNoticeHistorySchema = {
  name: string;
  notice_key?: string;
  description?: string;
  internal_description?: string;
  origin?: string;
  regions: Array<PrivacyNoticeRegion>;
  consent_mechanism: ConsentMechanism;
  data_uses: Array<string>;
  enforcement_level: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  displayed_in_privacy_center?: boolean;
  displayed_in_overlay?: boolean;
  displayed_in_api?: boolean;
  id: string;
  version: number;
  privacy_notice_id: string;
};
