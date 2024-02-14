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
 * be removed
 */
export type PrivacyNoticeUpdate = {
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
  gpp_field_mapping?: Array<GPPFieldMappingCreate>;
  translations: Array<NoticeTranslation>;
};

