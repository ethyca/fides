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
  has_vendor_id?: boolean | null;
  name?: string | null;
  description?: string | null;
  vendor_deleted_date?: string | null;
  special_purposes?: Array<EmbeddedPurpose>;
  features?: Array<EmbeddedLineItem>;
  special_features?: Array<EmbeddedLineItem>;
  cookie_max_age_seconds?: number | null;
  uses_cookies?: boolean | null;
  cookie_refresh?: boolean | null;
  uses_non_cookie_access?: boolean | null;
  legitimate_interest_disclosure_url?: string | null;
  privacy_policy_url?: string | null;
};
