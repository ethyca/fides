/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for AWS Bedrock connection test.
 */
export type BedrockConnectionTestResponse = {
  /**
   * Whether the connection test was successful
   */
  success: boolean;
  /**
   * Human-readable message about the test result
   */
  message: string;
  /**
   * Content returned by the model during test
   */
  response_content?: string | null;
  /**
   * Model that was tested
   */
  model: string;
  /**
   * Token usage information from the test
   */
  usage?: null;
  /**
   * Type of error if the test failed
   */
  error_type?: string | null;
};
