/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Distribution of diff statuses across generated tables
 */
export type DiffStatusDistribution = {
  /**
   * Proportion of tables with ADDITION status (0.0 to 1.0)
   */
  addition?: number;
  /**
   * Proportion of tables with CLASSIFYING status (0.0 to 1.0)
   */
  classifying?: number;
  /**
   * Proportion of tables with CLASSIFICATION_ADDITION status (0.0 to 1.0)
   */
  classification_addition?: number;
};

