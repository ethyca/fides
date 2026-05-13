/* istanbul ignore file */
/* tslint:disable */

import type { MessagingConfigStatus } from "./MessagingConfigStatus";

/**
 * A schema for checking configuration status of message config.
 */
export type MessagingConfigStatusMessage = {
  config_status?: MessagingConfigStatus | null;
  detail?: string | null;
};
