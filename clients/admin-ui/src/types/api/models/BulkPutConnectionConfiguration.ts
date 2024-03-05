/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { ConnectionConfigurationResponse } from "./ConnectionConfigurationResponse";

/**
 * Schema with mixed success/failure responses for Bulk Create/Update of ConnectionConfiguration responses.
 */
export type BulkPutConnectionConfiguration = {
  succeeded: Array<ConnectionConfigurationResponse>;
  failed: Array<BulkUpdateFailed>;
};
