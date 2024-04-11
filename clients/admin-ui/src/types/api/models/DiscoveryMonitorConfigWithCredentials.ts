/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DiscoveryMonitorTypes } from "./DiscoveryMonitorTypes";
import type { fides__api__schemas__connection_configuration__connection_secrets_bigquery__KeyfileCreds } from "./fides__api__schemas__connection_configuration__connection_secrets_bigquery__KeyfileCreds";
import type { MonitorFrequency } from "./MonitorFrequency";

/**
 * Base model for discovery monitor config
 */
export type DiscoveryMonitorConfigWithCredentials = {
  name: string;
  monitor_frequency?: MonitorFrequency;
  data_steward?: Array<string>;
  id?: string;
  type?: DiscoveryMonitorTypes;
  credentials: fides__api__schemas__connection_configuration__connection_secrets_bigquery__KeyfileCreds;
};
