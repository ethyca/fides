/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedLineItem } from "./EmbeddedLineItem";
import type { EmbeddedPurpose } from "./EmbeddedPurpose";
import type { TCFDataCategoryRecord } from "./TCFDataCategoryRecord";
import type { UserConsentPreference } from "./UserConsentPreference";

/**
 * Schema for a TCF Vendor or system: returned in the TCF Overlay Experience
 */
export type TCFVendorRecord = {
  default_preference?: UserConsentPreference;
  current_preference?: UserConsentPreference;
  outdated_preference?: UserConsentPreference;
  current_served?: boolean;
  outdated_served?: boolean;
  id: string;
  has_vendor_id: boolean;
  name?: string;
  description?: string;
  purposes?: Array<EmbeddedPurpose>;
  special_purposes?: Array<EmbeddedPurpose>;
  data_categories?: Array<TCFDataCategoryRecord>;
  features?: Array<EmbeddedLineItem>;
  special_features?: Array<EmbeddedLineItem>;
};
