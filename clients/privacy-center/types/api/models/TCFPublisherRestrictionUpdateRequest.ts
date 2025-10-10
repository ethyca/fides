/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RangeEntry } from "./RangeEntry";
import type { TCFRestrictionType } from "./TCFRestrictionType";
import type { TCFVendorRestriction } from "./TCFVendorRestriction";

/**
 * Schema for TCF Publisher Restriction update requests
 */
export type TCFPublisherRestrictionUpdateRequest = {
  /**
   * The type of restriction
   */
  restriction_type?: TCFRestrictionType | null;
  /**
   * The type of vendor restriction
   */
  vendor_restriction?: TCFVendorRestriction | null;
  /**
   * List of vendor ranges this restriction applies to
   */
  range_entries?: Array<RangeEntry> | null;
};
