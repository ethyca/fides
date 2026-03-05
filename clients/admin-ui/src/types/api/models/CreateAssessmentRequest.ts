/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request to create and queue an assessment generation task.
 *
 * New assessment types can be added by creating new templates in the database
 * without requiring code changes.
 */
export type CreateAssessmentRequest = {
  /**
   * Types of assessment - each must match an active template's assessment_type or key
   */
  assessment_types?: string[];
  /**
   * System fides keys to assess (null = all systems)
   */
  system_fides_keys?: string[] | null;
  /**
   * Whether to use LLM for AI-assisted answers
   */
  use_llm?: boolean;
  /**
   * Specific LLM model to use
   */
  model?: string | null;
};
