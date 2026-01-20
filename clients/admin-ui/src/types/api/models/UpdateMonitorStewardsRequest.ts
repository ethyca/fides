/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for updating the stewards on a specific monitor.
 */
export type UpdateMonitorStewardsRequest = {
  /**
   * List of user IDs to set as stewards for this monitor
   */
  user_ids: Array<string>;
};
