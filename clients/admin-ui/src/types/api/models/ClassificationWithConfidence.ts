/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConfidenceBucket } from "./ConfidenceBucket";

/**
 * Pydantic Schema used to represent a classification with a confidence bucket.
 *
 * The confidence_bucket is automatically calculated based on the confidence_rating
 * (1-5 integer) compared against configurable high/low thresholds, not the score field.
 * NULL confidence_rating is treated as 0, which maps to the LOW bucket.
 *
 * Thresholds are read from config. For testing, set config values via fixtures.
 */
export type ClassificationWithConfidence = {
  label: string;
  score: number;
  rationale?: string | null;
  confidence_rating?: number | null;
  /**
   * The confidence bucket according to the classification rating and the confidence thresholds. None if no confidence_rating is available.
   */
  confidence_bucket?: ConfidenceBucket | null;
};
