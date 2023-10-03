/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CurrentPrivacyPreferenceSchema } from "./CurrentPrivacyPreferenceSchema";

/**
 * Response schema when saving privacy preferences
 */
export type SavePrivacyPreferencesResponse = {
  preferences: Array<CurrentPrivacyPreferenceSchema>;
};
