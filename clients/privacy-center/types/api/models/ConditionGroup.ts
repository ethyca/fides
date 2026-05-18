/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConditionLeaf } from './ConditionLeaf';
import type { GroupOperator } from './GroupOperator';

export type ConditionGroup = {
  /**
   * Logical operator: 'and' or 'or'
   */
  logical_operator: GroupOperator;
  /**
   * List of conditions or nested groups
   */
  conditions: Array<(ConditionLeaf | ConditionGroup)>;
};

