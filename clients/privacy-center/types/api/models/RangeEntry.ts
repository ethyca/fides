/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Pydantic model that represents a vendor range entry as per the TCF spec,
 * used for Publisher Restrictions.
 * A range entry must have a start_vendor_id and optionally an end_vendor_id.
 * If end_vendor_id is present, it must be greater than start_vendor_id.
 */
export type RangeEntry = {
  /**
   * The starting vendor ID in the range
   */
  start_vendor_id: number;
  /**
   * The ending vendor ID in the range (inclusive)
   */
  end_vendor_id?: number | null;
};
