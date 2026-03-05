/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConditionGroup } from "./ConditionGroup";
import type { ConditionLeaf } from "./ConditionLeaf";

/**
 * Request schema for updating policy conditions.
 */
export type PolicyConditionRequest = {
  /**
   * Root condition (leaf or group) to set. Null/omitted to delete all conditions.
   */
  condition?: ConditionLeaf | ConditionGroup | null;
};
