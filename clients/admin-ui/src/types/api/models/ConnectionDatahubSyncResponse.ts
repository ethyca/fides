/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response for syncing Datahub connections.
 */
export type ConnectionDatahubSyncResponse = {
  succeeded: Array<string>;
  failed: Array<string>;
};
