/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request body for Async Callback
 */
export type RequestTaskCallbackRequest = {
  /**
   * Access results collected asynchronously, as a list of rows.  Use caution; this data may be used by dependent tasks downstream and/or uploaded to the end user.
   */
  access_results?: null;
  /**
   * Number of records masked, as an integer
   */
  rows_masked?: number | null;
};
