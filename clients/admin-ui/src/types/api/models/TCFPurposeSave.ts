/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for saving preferences with respect to a TCF Purpose
 */
export type TCFPurposeSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};
