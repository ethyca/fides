/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConsentMethod } from "./ConsentMethod";
import type { ConsentOptionCreate } from "./ConsentOptionCreate";
import type { Identity } from "./Identity";
import type { PrivacyNoticeRegion } from "./PrivacyNoticeRegion";

/**
 * Request body for creating PrivacyPreferences.
 */
export type PrivacyPreferencesRequest = {
  browser_identity: Identity;
  code?: string;
  preferences: Array<ConsentOptionCreate>;
  policy_key?: string;
  privacy_experience_history_id?: string;
  user_geography?: PrivacyNoticeRegion;
  method?: ConsentMethod;
};
