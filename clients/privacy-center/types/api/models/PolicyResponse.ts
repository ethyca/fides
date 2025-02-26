/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DrpAction } from "./DrpAction";
import type { RuleResponse } from "./RuleResponse";

/**
 * A holistic view of a Policy record, including all foreign keys by default.
 */
export type PolicyResponse = {
  name: string;
  key?: string | null;
  drp_action?: DrpAction | null;
  execution_timeframe?: number | null;
  rules?: Array<RuleResponse> | null;
};
