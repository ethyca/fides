/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Base schema for saving preferences with respect to a TCF Vendor
 * TODO: TCF Add validation for allowable vendors (in GVL or dictionary?)
 */
export type TCFVendorSave = {
  id: string;
  preference: UserConsentPreference;
  served_notice_history_id?: string;
};
