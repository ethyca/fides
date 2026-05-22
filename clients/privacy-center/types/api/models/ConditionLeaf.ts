/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Operator } from "./Operator";

export type ConditionLeaf = {
  /**
   * Field path to check (e.g., 'user.name', 'billing.subscription.status')
   */
  field_address: string;
  /**
   * Operator to apply
   */
  operator: Operator;
  /**
   * Expected value for comparison
   */
  value?: string | number | boolean | null;
};
