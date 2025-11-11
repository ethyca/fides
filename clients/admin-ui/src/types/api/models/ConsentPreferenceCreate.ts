/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PreferenceMetaCreate } from "./PreferenceMetaCreate";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema representing a single preference value for a given notice (API input).
 */
export type ConsentPreferenceCreate = {
  /**
   * Identifier for the experience config history
   */
  experience_config_history_id?: string | null;
  /**
   * Identifier for the notice history
   */
  notice_history_id: string;
  /**
   * Key identifying the notice/category
   */
  notice_key: string;
  /**
   * User preference value
   */
  value: UserConsentPreference;
  /**
   * Optional metadata for a single preference value (backend-only fields like 'derived', 'override', 'source' are not accepted)
   */
  meta?: PreferenceMetaCreate | null;
};
