/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DynamoDBMonitorParams } from "./DynamoDBMonitorParams";
import type { MonitorClassifyParams } from "./MonitorClassifyParams";
import type { MonitorFrequency } from "./MonitorFrequency";
import type { S3MonitorParams } from "./S3MonitorParams";

/**
 * Extends the EditableMonitorConfig with non-editable MonitorConfig fields.
 */
export type MonitorConfig = {
  name: string;
  key?: string;
  connection_config_key: string;
  classify_params: MonitorClassifyParams;
  /**
   * The datasource specific parameters, specified in a dictionary
   */
  datasource_params?: DynamoDBMonitorParams | S3MonitorParams;
  /**
   * The databases that the monitor is scoped to actively monitor
   */
  databases?: Array<string>;
  /**
   * The databases that the monitor should exclude from monitoring
   */
  excluded_databases?: Array<string>;
  execution_start_date?: string;
  execution_frequency?: MonitorFrequency;
  /**
   * Indicates whether the monitor is enabled or not. Disabled monitors won't be executed
   */
  enabled?: boolean;
  last_monitored?: string;
};
