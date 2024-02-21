/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedPurpose } from './EmbeddedPurpose';
import type { UserConsentPreference } from './UserConsentPreference';

/**
 * Schema for a TCF Vendor with Legitimate interests legal basis
 */
export type TCFVendorLegitimateInterestsRecord = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  default_preference?: UserConsentPreference;
  purpose_legitimate_interests?: Array<EmbeddedPurpose>;
};

