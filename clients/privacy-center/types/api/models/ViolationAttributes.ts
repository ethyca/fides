/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for attributes which led to an evaluation violation
 */
export type ViolationAttributes = {
  /**
   * A list of data categories which led to an evaluation violation.
   */
  data_categories: Array<string>;
  /**
   * A list of data subjects which led to an evaluation violation.
   */
  data_subjects: Array<string>;
  /**
   * A list of data uses which led to an evaluation violation.
   */
  data_uses: Array<string>;
};
