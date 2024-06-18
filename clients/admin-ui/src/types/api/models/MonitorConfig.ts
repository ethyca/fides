/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DynamoDBMonitorParams } from "./DynamoDBMonitorParams";
import type { MonitorClassifyParams } from "./MonitorClassifyParams";
import type { MonitorFrequency } from "./MonitorFrequency";

/**
 * Base model for monitor config
 */
export type MonitorConfig = {
  name: string;
  key?: string;
  connection_config_key: string;
  classify_params: MonitorClassifyParams;
  /**
   * The datasource specific parameters, specified in a dictionary
   */
  datasource_params?: DynamoDBMonitorParams;
  /**
   * The databases that the monitor is scoped to actively monitor
   */
  databases?: Array<string>;
  execution_start_date?: string;
  execution_frequency?: MonitorFrequency;
};
