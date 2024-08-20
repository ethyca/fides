/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DynamoDBMonitorParams } from "./DynamoDBMonitorParams";
import type { MonitorClassifyParams } from "./MonitorClassifyParams";
import type { MonitorFrequency } from "./MonitorFrequency";
import type { S3MonitorParams } from "./S3MonitorParams";

/**
 * Base model for monitor config containing the fields that can be updated via API
 */
export type EditableMonitorConfig = {
  name: string;
  key?: string | null;
  connection_config_key: string;
  classify_params: MonitorClassifyParams;
  /**
   * The datasource specific parameters, specified in a dictionary
   */
  datasource_params?: DynamoDBMonitorParams | S3MonitorParams | null;
  /**
   * The databases that the monitor is scoped to actively monitor
   */
  databases?: Array<string>;
  execution_start_date?: string | null;
  execution_frequency?: MonitorFrequency | null;
  /**
   * The databases that the monitor should exclude from monitoring
   */
  excluded_databases?: Array<string>;
  /**
   * Indicates whether the monitor is enabled or not. Disabled monitors won't be executed
   */
  enabled?: boolean | null;
};
