/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { WebhookDirection } from "./WebhookDirection";

/**
 * Request schema for creating/updating a Policy Webhook
 */
export type PolicyWebhookCreate = {
  direction: WebhookDirection;
  key?: string;
  name?: string;
  connection_config_key: string;
};
