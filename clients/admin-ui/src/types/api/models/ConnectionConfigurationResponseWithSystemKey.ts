/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AccessLevel } from "./AccessLevel";
import type { ActionType } from "./ActionType";
import type { ConnectionType } from "./ConnectionType";
import type { SaaSConfigBase } from "./SaaSConfigBase";

/**
 * Describes the full returned schema for a ConnectionConfiguration.
 */
export type ConnectionConfigurationResponseWithSystemKey = {
  connection_type: ConnectionType;
  secrets?: null;
  saas_config?: SaaSConfigBase | null;
  name?: string | null;
  key: string;
  description?: string | null;
  access: AccessLevel;
  created_at: string;
  updated_at?: string | null;
  disabled?: boolean | null;
  last_test_timestamp?: string | null;
  last_test_succeeded?: boolean | null;
  authorized?: boolean | null;
  enabled_actions?: Array<ActionType> | null;
  system_key?: string | null;
};
