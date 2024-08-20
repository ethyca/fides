/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { StatusEnum } from "./StatusEnum";
import type { Violation } from "./Violation";

/**
 * The Evaluation resource model.
 *
 * This resource is created after an evaluation is executed.
 */
export type Evaluation = {
  /**
   * A uuid generated for each unique evaluation.
   */
  fides_key: string;
  status: StatusEnum;
  /**
   * The model for violations within an evaluation.
   */
  violations?: Array<Violation>;
  /**
   * A human-readable string response for the evaluation.
   */
  message?: string;
};
