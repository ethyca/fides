/* istanbul ignore file */
/* tslint:disable */

import type { Consent } from "./Consent";

/**
 * Schema for consent preferences.
 */
export type ConsentPreferences = {
  consent?: Array<Consent> | null;
};
