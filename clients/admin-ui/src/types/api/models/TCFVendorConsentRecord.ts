/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedPurpose } from './EmbeddedPurpose';
import type { UserConsentPreference } from './UserConsentPreference';

/**
 * Schema for a TCF Vendor with Consent legal basis
 */
export type TCFVendorConsentRecord = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  default_preference?: UserConsentPreference;
  purpose_consents?: Array<EmbeddedPurpose>;
};

