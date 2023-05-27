/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentOptionCreate } from "./ConsentOptionCreate";
import type { Identity } from "./Identity";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";
import type { RequestOrigin } from "./RequestOrigin";

/**
 * Schema for saving privacy preferences and accompanying user data
 * including the verification code.
 */
export type PrivacyPreferencesCreateWithCode = {
  browser_identity: Identity;
  code?: string;
  preferences: Array<ConsentOptionCreate>;
  policy_key?: string;
  request_origin?: RequestOrigin;
  url_recorded?: string;
  user_agent?: string;
  user_geography?: PrivacyNoticeRegion;
};
