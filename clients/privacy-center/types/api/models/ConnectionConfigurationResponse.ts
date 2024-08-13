/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AccessLevel } from './AccessLevel';
import type { ActionType } from './ActionType';
import type { ConnectionType } from './ConnectionType';
import type { SaaSConfigBase } from './SaaSConfigBase';

/**
 * Describes the returned schema for a ConnectionConfiguration.
 */
export type ConnectionConfigurationResponse = {
  name?: string;
  key: string;
  description?: string;
  connection_type: ConnectionType;
  access: AccessLevel;
  created_at: string;
  updated_at?: string;
  disabled?: boolean;
  last_test_timestamp?: string;
  last_test_succeeded?: boolean;
  saas_config?: SaaSConfigBase;
  secrets?: any;
  authorized?: boolean;
  enabled_actions?: Array<ActionType>;
};

