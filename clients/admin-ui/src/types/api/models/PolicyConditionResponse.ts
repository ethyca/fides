/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConditionGroup } from "./ConditionGroup";
import type { ConditionLeaf } from "./ConditionLeaf";

/**
 * Response schema for policy conditions.
 */
export type PolicyConditionResponse = {
  /**
   * Root condition (leaf or group) with nested structure. Null if no conditions exist.
   */
  condition?: ConditionLeaf | ConditionGroup | null;
};
