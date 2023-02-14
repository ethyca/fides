/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { RuleResponse } from "./RuleResponse";

/**
 * Schema with mixed success/failure responses for Bulk Create/Update of Rule responses.
 */
export type BulkPutRuleResponse = {
  succeeded: Array<RuleResponse>;
  failed: Array<BulkUpdateFailed>;
};
