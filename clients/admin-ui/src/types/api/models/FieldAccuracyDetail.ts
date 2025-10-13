/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Detailed accuracy information for a single field.
 */
export type FieldAccuracyDetail = {
  /**
   * URN of the field being evaluated
   */
  field_urn: string;
  /**
   * Categories assigned by the system
   */
  staged_resource_categories: Array<string>;
  /**
   * Ground truth categories from dataset
   */
  ground_truth_categories: Array<string>;
  /**
   * Whether the field was classified correctly
   */
  is_correct: boolean;
  /**
   * Categories that were incorrectly classified (false positives)
   */
  false_positives: Array<string>;
  /**
   * Categories that were correctly classified (true positives)
   */
  true_positives: Array<string>;
  /**
   * Categories that were missed (false negatives)
   */
  false_negatives: Array<string>;
  /**
   * Categories that were correctly classified as the default category (true negatives)
   */
  true_negatives: Array<string>;
  /**
   * Whether the classification is an error, e.g. if our default tag is applied alongside other tags
   */
  classification_error: boolean;
};

