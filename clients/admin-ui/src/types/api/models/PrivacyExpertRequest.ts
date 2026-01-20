/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for the privacy expert endpoint.
 */
export type PrivacyExpertRequest = {
  /**
   * The privacy-related question to ask the LLM
   */
  question: string;
  /**
   * Optional LLM model override. Uses default classification model if not specified.
   */
  model?: string | null;
  /**
   * Whether to include inactive/disabled taxonomy items in the context
   */
  include_inactive?: boolean;
  /**
   * Maximum tokens for the LLM response
   */
  max_tokens?: number;
};
