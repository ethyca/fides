/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { RangeEntry } from "./RangeEntry";
import type { TCFRestrictionType } from "./TCFRestrictionType";
import type { TCFVendorRestriction } from "./TCFVendorRestriction";

/**
 * Schema for TCF Publisher Restriction creation/update requests
 */
export type TCFPublisherRestrictionRequest = {
  /**
   * The ID of the purpose this restriction applies to
   */
  purpose_id: number;
  /**
   * The type of restriction
   */
  restriction_type: TCFRestrictionType;
  /**
   * The type of vendor restriction
   */
  vendor_restriction: TCFVendorRestriction;
  /**
   * List of vendor ranges this restriction applies to
   */
  range_entries?: Array<RangeEntry>;
};
