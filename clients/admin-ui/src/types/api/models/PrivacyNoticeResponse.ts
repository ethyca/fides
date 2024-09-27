/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMechanism } from "./ConsentMechanism";
import type { Cookies } from "./Cookies";
import type { EnforcementLevel } from "./EnforcementLevel";
import type { GPPFieldMapping } from "./GPPFieldMapping";
import { MinimalPrivacyNotice } from "./MinimalPrivacyNotice";
import type { NoticeTranslationResponse } from "./NoticeTranslationResponse";
import type { PrivacyNoticeFramework } from "./PrivacyNoticeFramework";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * An API representation of a PrivacyNotice used for response payloads
 *
 * Overrides fields from PrivacyNotice schema to indicate which ones
 * are guaranteed to be supplied
 */
export type PrivacyNoticeResponse = {
  name: string;
  notice_key: string;
  internal_description?: string | null;
  consent_mechanism: ConsentMechanism;
  data_uses: Array<string>;
  enforcement_level: EnforcementLevel;
  disabled: boolean;
  has_gpc_flag: boolean;
  framework?: PrivacyNoticeFramework | null;
  default_preference?: UserConsentPreference | null;
  id: string;
  origin?: string | null;
  created_at: string;
  updated_at: string;
  cookies?: Array<Cookies>;
  systems_applicable?: boolean;
  translations?: Array<NoticeTranslationResponse>;
  children: Array<MinimalPrivacyNotice>;
  gpp_field_mapping?: Array<GPPFieldMapping> | null;
};
