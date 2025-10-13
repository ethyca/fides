/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BigQueryMonitorParams } from './BigQueryMonitorParams';
import type { DynamoDBMonitorParams } from './DynamoDBMonitorParams';
import type { MonitorClassifyParams } from './MonitorClassifyParams';
import type { MonitorFrequency } from './MonitorFrequency';
import type { S3MonitorParams } from './S3MonitorParams';
import type { TestMonitorParams } from './TestMonitorParams';
import type { TestWebsiteMonitorParams } from './TestWebsiteMonitorParams';
import type { WebsiteMonitorParams } from './WebsiteMonitorParams';

/**
 * Base model for monitor config containing the fields that can be updated via API
 */
export type EditableMonitorConfig = {
  name: string;
  key?: (string | null);
  connection_config_key: string;
  /**
   * Parameters for classification of discovered resources
   */
  classify_params?: (MonitorClassifyParams | null);
  /**
   * The datasource specific parameters, specified in a dictionary
   */
  datasource_params?: (DynamoDBMonitorParams | S3MonitorParams | WebsiteMonitorParams | TestWebsiteMonitorParams | TestMonitorParams | BigQueryMonitorParams | null);
  /**
   * The databases that the monitor is scoped to actively monitor
   */
  databases?: Array<string>;
  execution_start_date?: (string | null);
  execution_frequency?: (MonitorFrequency | null);
  /**
   * The databases that the monitor should exclude from monitoring
   */
  excluded_databases?: Array<string>;
  /**
   * Indicates whether the monitor is enabled or not. Disabled monitors won't be executed
   */
  enabled?: (boolean | null);
  /**
   * Reference to a shared monitor configuration
   */
  shared_config_id?: (string | null);
};

