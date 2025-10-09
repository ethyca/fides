/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Accuracy metrics for classification evaluation.
 */
export type AccuracyMetrics = {
  /**
   * Precision score (0.0 to 1.0)
   */
  precision: number;
  /**
   * Recall score (0.0 to 1.0)
   */
  recall: number;
  /**
   * F1 score (0.0 to 1.0)
   */
  f1_score: number;
  /**
   * Total number of ground truth categories
   */
  total_ground_truth: number;
  /**
   * Total number of classified categories
   */
  total_classified: number;
  /**
   * Number of correctly classified categories
   */
  true_positives: number;
  /**
   * Number of incorrectly classified categories
   */
  false_positives: number;
  /**
   * Number of missed categories
   */
  false_negatives: number;
  /**
   * Number of correctly classified default categories
   */
  true_negatives: number;
  /**
   * Number of classification errors
   */
  errors: number;
};
