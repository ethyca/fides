/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionTestStatus } from "./ConnectionTestStatus";

/**
 * A schema for checking status.
 */
export type TestStatusMessage = {
  msg: string;
  test_status?: ConnectionTestStatus;
  failure_reason?: string;
};
