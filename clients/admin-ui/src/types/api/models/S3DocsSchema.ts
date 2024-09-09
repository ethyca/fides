/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AWSAuthMethod } from "./AWSAuthMethod";

/**
 * S3 Secrets Schema for API Docs
 */
export type S3DocsSchema = {
  /**
   * Determines which type of authentication method to use for connecting to Amazon Web Services. Currently accepted values are: `secret_keys` or `automatic`.
   */
  auth_method?: AWSAuthMethod;
  /**
   * Part of the credentials that provide access to your AWS account.
   */
  aws_access_key_id?: string | null;
  /**
   * Part of the credentials that provide access to your AWS account.
   */
  aws_secret_access_key?: string | null;
  /**
   * If provided, the ARN of the role that should be assumed to connect to AWS.
   */
  aws_assume_role_arn?: string | null;
};
