/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConstraintType } from "./ConstraintType";

/**
 * Base class for table constraints
 */
export type Constraint = {
  name: string;
  fields: Array<string>;
  type: ConstraintType;
};
