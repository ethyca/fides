/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { WebhookDirection } from "./WebhookDirection";

/**
 * Request schema for updating a single webhook - fields are optional
 */
export type PolicyWebhookUpdate = {
  direction?: WebhookDirection;
  name?: string;
  connection_config_key?: string;
  order?: number;
};
