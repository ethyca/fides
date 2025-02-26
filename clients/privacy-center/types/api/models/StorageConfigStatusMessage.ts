/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { StorageConfigStatus } from "./StorageConfigStatus";

/**
 * A schema for checking configuration status of storage config.
 */
export type StorageConfigStatusMessage = {
  config_status?: StorageConfigStatus | null;
  detail?: string | null;
};
