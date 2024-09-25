/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ViolationAttributes } from "./ViolationAttributes";

/**
 * The model for violations within an evaluation.
 */
export type Violation = {
  violating_attributes: ViolationAttributes;
  /**
   * A human-readable string detailing the evaluation violation.
   */
  detail: string;
};
