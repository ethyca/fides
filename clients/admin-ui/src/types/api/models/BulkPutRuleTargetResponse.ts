/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { BulkUpdateFailed } from "./BulkUpdateFailed";
import type { RuleTarget } from "./RuleTarget";

/**
 * Schema with mixed success/failure responses for Bulk Create/Update of RuleTarget responses.
 */
export type BulkPutRuleTargetResponse = {
  succeeded: Array<RuleTarget>;
  failed: Array<BulkUpdateFailed>;
};
