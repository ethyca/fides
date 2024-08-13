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
  key?: string;
  drp_action?: DrpAction;
  execution_timeframe?: number;
  rules?: Array<RuleResponse>;
};
