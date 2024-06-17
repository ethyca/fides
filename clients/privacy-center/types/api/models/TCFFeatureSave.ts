/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for saving a user's preference with respect to a TCF feature
 */
export type TCFFeatureSave = {
  id: number;
  preference: UserConsentPreference;
};
