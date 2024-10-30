/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionConfigurationResponse } from "./ConnectionConfigurationResponse";
import type { ManualWebhookField } from "./ManualWebhookField";

/**
 * Expected response for accessing Access Manual Webhooks
 */
export type AccessManualWebhookResponse = {
  fields: Array<ManualWebhookField>;
  connection_config: ConnectionConfigurationResponse;
  id: string;
};
