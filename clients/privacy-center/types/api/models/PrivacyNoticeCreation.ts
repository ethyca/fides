/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from './ConsentMechanism';
import type { EnforcementLevel } from './EnforcementLevel';
import type { GPPFieldMappingCreate } from './GPPFieldMappingCreate';
import type { NoticeTranslationCreate } from './NoticeTranslationCreate';
import type { PrivacyNoticeFramework } from './PrivacyNoticeFramework';

/**
 * Establishes some fields required for creating and validation that can be performed up-front
 */
export type PrivacyNoticeCreation = {
  name: string;
  notice_key?: string;
  internal_description?: string;
  consent_mechanism: ConsentMechanism;
  data_uses?: Array<string>;
  enforcement_level: EnforcementLevel;
  disabled?: boolean;
  has_gpc_flag?: boolean;
  framework?: PrivacyNoticeFramework;
  gpp_field_mapping?: Array<GPPFieldMappingCreate>;
  translations?: Array<NoticeTranslationCreate>;
};

