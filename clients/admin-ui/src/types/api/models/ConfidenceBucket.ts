/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum for confidence bucket classifications.
 *
 * Confidence buckets are determined by the `confidence_rating` field (1-5 integer)
 * and configurable thresholds, NOT by the `score` field. The `score` field is
 * maintained for backwards compatibility but is always 1.0 for LLM classifications.
 */
export enum ConfidenceBucket {
  LOW = "low",
  HIGH = "high",
  MEDIUM = "medium",
  MANUAL = "manual",
}
