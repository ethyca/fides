/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DiscoveryMonitorTypes } from "./DiscoveryMonitorTypes";
import type { MonitorFrequency } from "./MonitorFrequency";

/**
 * Base model for discovery monitor config
 */
export type DiscoveryMonitorConfig = {
  name: string;
  monitor_frequency?: MonitorFrequency;
  data_steward?: Array<string>;
  id?: string;
  type?: DiscoveryMonitorTypes;
};
