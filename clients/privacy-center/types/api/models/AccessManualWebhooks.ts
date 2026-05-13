/* istanbul ignore file */
/* tslint:disable */

import type { ManualWebhookField } from "./ManualWebhookField";

/**
 * Expected request body for creating Access Manual Webhooks
 */
export type AccessManualWebhooks = {
  fields: Array<ManualWebhookField>;
};
