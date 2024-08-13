/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionConfigurationResponse } from './ConnectionConfigurationResponse';

/**
 * Response schema after creating/updating/getting a PreApprovalWebhook
 */
export type PreApprovalWebhookResponse = {
  key?: string;
  name: string;
  connection_config?: ConnectionConfigurationResponse;
};

