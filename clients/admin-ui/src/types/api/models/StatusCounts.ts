/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Counts of resources by diff_status group. Consistent across all monitor types.
 */
export type StatusCounts = {
  addition?: number;
  classifying?: number;
  classified?: number;
  reviewed?: number;
  monitored?: number;
  removal?: number;
};
