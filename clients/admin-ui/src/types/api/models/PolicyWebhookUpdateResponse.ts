/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PolicyWebhookResponse } from "./PolicyWebhookResponse";
import type { WebhookOrder } from "./WebhookOrder";

/**
 * Response schema after a PATCH to a single webhook - because updating the order of this webhook can update the
 * order of other webhooks, new_order will include the new order if order was adjusted at all
 */
export type PolicyWebhookUpdateResponse = {
  resource: PolicyWebhookResponse;
  new_order: Array<WebhookOrder>;
};
