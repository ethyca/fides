/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BigQueryMonitorParams } from "./BigQueryMonitorParams";
import type { DynamoDBMonitorParams } from "./DynamoDBMonitorParams";
import type { IdentityProvider } from "./IdentityProvider";
import type { MonitorClassifyParams } from "./MonitorClassifyParams";
import type { MonitorFrequency } from "./MonitorFrequency";
import type { S3MonitorParams } from "./S3MonitorParams";
import type { TestMonitorParams } from "./TestMonitorParams";
import type { TestWebsiteMonitorParams } from "./TestWebsiteMonitorParams";
import type { WebsiteMonitorParams } from "./WebsiteMonitorParams";

/**
 * Configuration for Identity Provider discovery monitors.
 */
export type IdentityProviderMonitorConfig = {
  name: string;
  key?: string | null;
  connection_config_key: string;
  /**
   * Parameters for classification of discovered resources
   */
  classify_params?: MonitorClassifyParams | null;
  /**
   * The datasource specific parameters, specified in a dictionary
   */
  datasource_params?:
    | DynamoDBMonitorParams
    | S3MonitorParams
    | WebsiteMonitorParams
    | TestWebsiteMonitorParams
    | TestMonitorParams
    | BigQueryMonitorParams
    | null;
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
   * Whether the monitor is enabled for scheduled execution
   */
  enabled?: boolean;
  /**
   * Reference to a shared monitor configuration
   */
  shared_config_id?: string | null;
  /**
   * List of user IDs to set as stewards for this monitor
   */
  stewards?: Array<string>;
  /**
   * Identity Provider type (currently only 'okta' is supported)
   */
  provider?: IdentityProvider;
};
