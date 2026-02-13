/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request to create a new assessment.
 *
 * The assessment_type should match either:
 * - The `assessment_type` field of an AssessmentTemplate in the database
 * - The `key` field of an AssessmentTemplate (as a fallback)
 *
 * New assessment types can be added by creating new templates in the database
 * without requiring code changes.
 */
export type CreateAssessmentRequest = {
  /**
   * Type of assessment - must match an active template's assessment_type or key
   */
  assessment_type?: string;
  /**
   * System fides key
   */
  system_fides_key?: (string | null);
  /**
   * Declaration ID
   */
  declaration_id?: (string | null);
  /**
   * Whether to use LLM for AI-assisted answers
   */
  use_llm?: boolean;
  /**
   * Specific LLM model to use
   */
  model?: (string | null);
};

