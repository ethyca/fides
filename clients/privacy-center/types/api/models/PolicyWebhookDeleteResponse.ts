/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { WebhookOrder } from "./WebhookOrder";

/**
 * Response schema after deleting a webhook; new_order includes remaining reordered webhooks if applicable
 */
export type PolicyWebhookDeleteResponse = {
  new_order: Array<WebhookOrder>;
};
