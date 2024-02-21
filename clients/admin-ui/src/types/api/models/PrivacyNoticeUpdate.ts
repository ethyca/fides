/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from './ConsentMechanism';
import type { EnforcementLevel } from './EnforcementLevel';
import type { GPPFieldMappingCreate } from './GPPFieldMappingCreate';
import type { NoticeTranslation } from './NoticeTranslation';
import type { PrivacyNoticeFramework } from './PrivacyNoticeFramework';

/**
 * Overriding Privacy Notice schema for updates - translations must be supplied or they will
 * be removed.
 *
 * Other aspects will be validated on a dry update after patch updates are applied against PrivacyNoticeCreation
 */
export type PrivacyNoticeUpdate = {
  name?: string;
  notice_key?: string;
  internal_description?: string;
  consent_mechanism?: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level?: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  framework?: PrivacyNoticeFramework;
  gpp_field_mapping?: Array<GPPFieldMappingCreate>;
  translations: Array<NoticeTranslation>;
};

