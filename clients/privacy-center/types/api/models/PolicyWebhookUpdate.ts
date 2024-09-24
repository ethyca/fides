/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { WebhookDirection } from "./WebhookDirection";

/**
 * Request schema for updating a single webhook - fields are optional
 */
export type PolicyWebhookUpdate = {
  direction?: WebhookDirection | null;
  name?: string | null;
  connection_config_key?: string | null;
  order?: number | null;
};
