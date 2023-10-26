/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for saving a user's preference with respect to a TCF special feature
 */
export type TCFSpecialFeatureSave = {
  id: number;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};
