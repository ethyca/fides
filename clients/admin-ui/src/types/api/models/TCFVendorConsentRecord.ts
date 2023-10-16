/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedLineItem } from "./EmbeddedLineItem";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for a TCF Vendor with Consent legal basis
 */
export type TCFVendorConsentRecord = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  purpose_consents?: Array<EmbeddedLineItem>;
};
