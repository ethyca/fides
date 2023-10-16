/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedLineItem } from "./EmbeddedLineItem";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for a TCF Vendor with Legitimate interests legal basis
 */
export type TCFVendorLegitimateInterestsRecord = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  cookie_max_age_seconds?: number;
  uses_cookies?: boolean;
  cookie_refresh?: boolean;
  uses_non_cookie_access?: boolean;
  legitimate_interest_disclosure_url?: string;
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  purpose_legitimate_interests?: Array<EmbeddedLineItem>;
};
