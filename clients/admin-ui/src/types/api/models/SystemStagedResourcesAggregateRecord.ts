/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * API response model for records of aggregated staged resources by system
 */
export type SystemStagedResourcesAggregateRecord = {
  /**
   * The aggregate record ID, either a system fides_key or a vendor ID
   */
  id?: string | null;
  name?: string | null;
  system_key?: string | null;
  data_uses?: Array<string>;
  vendor_id?: string | null;
  total_updates?: number;
  locations?: Array<string>;
  domains?: Array<string>;
};
