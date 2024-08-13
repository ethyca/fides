/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * DynamoDB Secrets Schema for API Docs
 */
export type DynamoDBDocsSchema = {
  /**
   * The AWS region where your DynamoDB table is located (ex. us-west-2).
   */
  region_name: string;
  /**
   * Part of the credentials that provide access to your AWS account.
   */
  aws_access_key_id: string;
  /**
   * Part of the credentials that provide access to your AWS account.
   */
  aws_secret_access_key: string;
};

