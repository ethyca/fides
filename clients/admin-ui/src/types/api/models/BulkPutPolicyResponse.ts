/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { PolicyResponse } from "./PolicyResponse";

/**
 * Schema with mixed success/failure responses for Bulk Create/Update of Policy responses.
 */
export type BulkPutPolicyResponse = {
  succeeded: Array<PolicyResponse>;
  failed: Array<BulkUpdateFailed>;
};
