/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedLineItem } from "./EmbeddedLineItem";
import type { EmbeddedPurpose } from "./EmbeddedPurpose";

/**
 * Collects the other relationships for a given vendor - no preferences are saved here
 */
export type TCFVendorRelationships = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  special_purposes?: Array<EmbeddedPurpose>;
  features?: Array<EmbeddedLineItem>;
  special_features?: Array<EmbeddedLineItem>;
  cookie_max_age_seconds?: number;
  uses_cookies?: boolean;
  cookie_refresh?: boolean;
  uses_non_cookie_access?: boolean;
  legitimate_interest_disclosure_url?: string;
  privacy_policy_url?: string;
};
