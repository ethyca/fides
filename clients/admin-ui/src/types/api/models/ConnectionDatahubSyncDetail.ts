/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConnectionDatahubSyncDetailStatus } from "./ConnectionDatahubSyncDetailStatus";

/**
 * Detail of a Datahub sync.
 */
export type ConnectionDatahubSyncDetail = {
  dataset_id: string;
  status: ConnectionDatahubSyncDetailStatus;
  message: string;
};
