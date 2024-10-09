/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MessagingConnectionTestStatus } from "./MessagingConnectionTestStatus";

/**
 * A schema for testing functionality of a messaging config.
 */
export type TestMessagingStatusMessage = {
  msg: string;
  test_status?: MessagingConnectionTestStatus | null;
  failure_reason?: string | null;
};
