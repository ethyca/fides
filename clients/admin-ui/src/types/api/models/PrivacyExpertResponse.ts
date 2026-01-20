/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for the privacy expert endpoint.
 */
export type PrivacyExpertResponse = {
  /**
   * The LLM's response to the privacy question
   */
  answer: string;
  /**
   * Summary of the privacy context provided to the LLM
   */
  context_summary: any;
  /**
   * The model used for generation
   */
  model: string;
};
