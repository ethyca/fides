/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * API response model for records of aggregated staged resources by monitor config
 */
export type MonitorConfigStagedResourcesAggregateRecord = {
  name: string;
  key?: string | null;
  last_monitored?: string | null;
  updates?: any;
  total_updates?: number;
};
