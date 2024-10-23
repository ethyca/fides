/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AccessLevel } from "./AccessLevel";
import type { ActionType } from "./ActionType";
import type { ConnectionType } from "./ConnectionType";
import type { SaaSConfigBase } from "./SaaSConfigBase";

/**
 * Describes the returned schema for a ConnectionConfiguration.
 */
export type ConnectionConfigurationResponse = {
  name?: string | null;
  key: string;
  description?: string | null;
  connection_type: ConnectionType;
  access: AccessLevel;
  created_at: string;
  updated_at?: string | null;
  disabled?: boolean | null;
  last_test_timestamp?: string | null;
  last_test_succeeded?: boolean | null;
  saas_config?: SaaSConfigBase | null;
  secrets?: any;
  authorized?: boolean | null;
  enabled_actions?: Array<ActionType> | null;
};
