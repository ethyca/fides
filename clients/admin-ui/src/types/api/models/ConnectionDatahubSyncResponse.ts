/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionDatahubSyncDetail } from "./ConnectionDatahubSyncDetail";

/**
 * Response for syncing Datahub connections.
 */
export type ConnectionDatahubSyncResponse = {
  succeeded: Array<string>;
  failed: Array<string>;
  details: Array<ConnectionDatahubSyncDetail>;
};
