/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PreferenceMeta } from "./PreferenceMeta";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * An individual preference response (includes backend-generated fields).
 */
export type ConsentPreferenceResponse = {
  /**
   * Identifier for the experience config history
   */
  experience_config_history_id?: string | null;
  /**
   * Identifier for the notice history
   */
  notice_history_id: string;
  /**
   * Key identifying the privacy notice
   */
  notice_key: string;
  /**
   * User preference value
   */
  value: UserConsentPreference;
  /**
   * Metadata for a single preference value (includes backend fields like 'derived', 'override', 'source')
   */
  meta?: PreferenceMeta | null;
};
