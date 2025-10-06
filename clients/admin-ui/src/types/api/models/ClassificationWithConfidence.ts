/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConfidenceScoreRange } from "./ConfidenceScoreRange";

/**
 * Pydantic Schema used to represent a classification with a confidence score
 */
export type ClassificationWithConfidence = {
  label: string;
  score: number;
  /**
   * The confidence score according to the classification score and the confidence score threshold
   */
  confidence_score: ConfidenceScoreRange;
};
