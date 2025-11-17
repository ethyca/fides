/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Request schema for AWS Bedrock connection test.
 */
export type BedrockConnectionTestRequest = {
  aws_region: string;
  /**
   * Bedrock model string
   */
  model: string;
  aws_bearer_token_bedrock?: string | null;
  aws_role_arn?: string | null;
  aws_web_identity_token?: string | null;
  aws_role_session_name?: string | null;
};
