/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmbeddedLineItem } from "./EmbeddedLineItem";

/**
 * Collects the other relationships for a given vendor - no preferences are saved here
 */
export type TCFVendorRelationships = {
  id: string;
  has_vendor_id?: boolean;
  name?: string;
  description?: string;
  special_purposes?: Array<EmbeddedLineItem>;
  features?: Array<EmbeddedLineItem>;
  special_features?: Array<EmbeddedLineItem>;
};
