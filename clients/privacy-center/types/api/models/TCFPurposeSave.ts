/* istanbul ignore file */
/* tslint:disable */

import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for saving preferences with respect to a TCF Purpose
 */
export type TCFPurposeSave = {
  id: number;
  preference: UserConsentPreference;
};
