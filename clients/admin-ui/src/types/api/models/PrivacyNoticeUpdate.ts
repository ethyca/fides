/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { GPPFieldMappingCreate } from "./GPPFieldMappingCreate";
import type { NoticeTranslation } from "./NoticeTranslation";
import type { PrivacyNoticeFramework } from "./PrivacyNoticeFramework";
import type { MinimalPrivacyNotice } from "./MinimalPrivacyNotice";

/**
 * Overriding Privacy Notice schema for updates - translations must be supplied or they will
 * be removed.
 *
 * Other aspects will be validated on a dry update after patch updates are applied against PrivacyNoticeCreation
 */
export type PrivacyNoticeUpdate = {
  name?: string | null;
  notice_key?: string | null;
  internal_description?: string | null;
  consent_mechanism?: ConsentMechanism | null;
  data_uses?: Array<string> | null;
  enforcement_level?: EnforcementLevel | null;
  disabled?: boolean | null;
  has_gpc_flag?: boolean | null;
  framework?: PrivacyNoticeFramework | null;
  gpp_field_mapping?: Array<GPPFieldMappingCreate> | null;
  translations: Array<NoticeTranslation>;
  children: Array<MinimalPrivacyNotice> | null;
};
