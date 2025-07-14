/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionType } from "./ConnectionType";
import type { ConsentAlertInfo } from "./ConsentAlertInfo";
import type { SaaSConfigBase } from "./SaaSConfigBase";

/**
 * API response model for records of aggregated staged resources by monitor config.
 *
 * This model inherits from ConnectionConfigSecretsMixin, which handles the masking of
 * sensitive values in the connection config `secrets` attribute, and also declares a
 * `connection_type` attribute.
 */
export type MonitorConfigStagedResourcesAggregateRecord = {
  connection_type: ConnectionType;
  secrets?: null;
  saas_config?: SaaSConfigBase | null;
  name: string;
  key?: string | null;
  last_monitored?: string | null;
  updates?: any;
  total_updates?: number;
  consent_status?: ConsentAlertInfo | null;
};
