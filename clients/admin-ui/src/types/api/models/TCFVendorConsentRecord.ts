/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedPurpose } from "./EmbeddedPurpose";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for a TCF Vendor with Consent legal basis
 */
export type TCFVendorConsentRecord = {
  id: string;
  has_vendor_id?: boolean | null;
  name?: string | null;
  description?: string | null;
  vendor_deleted_date?: string | null;
  default_preference?: UserConsentPreference | null;
  purpose_consents?: Array<EmbeddedPurpose>;
};
