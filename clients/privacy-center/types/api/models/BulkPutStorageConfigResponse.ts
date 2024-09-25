/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { StorageDestinationResponse } from "./StorageDestinationResponse";

/**
 * Schema with mixed success/failure responses for Bulk Create/Update of StorageConfig.
 */
export type BulkPutStorageConfigResponse = {
  succeeded?: Array<StorageDestinationResponse>;
  failed?: Array<BulkUpdateFailed>;
};
