/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MessagingConnectionTestStatus } from "./MessagingConnectionTestStatus";

/**
 * A schema for checking status of message config.
 */
export type TestMessagingStatusMessage = {
  msg: string;
  test_status?: MessagingConnectionTestStatus;
  failure_reason?: string;
};
