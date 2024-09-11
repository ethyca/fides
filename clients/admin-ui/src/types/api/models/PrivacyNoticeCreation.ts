/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { GPPFieldMappingCreate } from "./GPPFieldMappingCreate";
import type { NoticeTranslationCreate } from "./NoticeTranslationCreate";
import type { PrivacyNoticeFramework } from "./PrivacyNoticeFramework";
import type { MinimalPrivacyNotice } from "~/types/api/models/MinimalPrivacyNotice";

/**
 * Establishes some fields required for creating and validation that can be performed up-front
 */
export type PrivacyNoticeCreation = {
  name: string;
  notice_key?: string | null;
  internal_description?: string | null;
  consent_mechanism: ConsentMechanism;
  data_uses?: Array<string> | null;
  enforcement_level: EnforcementLevel;
  disabled?: boolean | null;
  has_gpc_flag?: boolean | null;
  framework?: PrivacyNoticeFramework | null;
  gpp_field_mapping?: Array<GPPFieldMappingCreate> | null;
  translations?: Array<NoticeTranslationCreate> | null;
  children: Array<MinimalPrivacyNotice> | null;
};
