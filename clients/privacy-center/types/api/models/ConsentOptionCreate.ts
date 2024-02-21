/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserConsentPreference } from './UserConsentPreference';

/**
 * Schema for saving the user's preference for a given Privacy Notice (non-TCF Notice)
 */
export type ConsentOptionCreate = {
  privacy_notice_history_id: string;
  preference: UserConsentPreference;
};
