/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for the connection config for AWS
 */
export type AWSConfig = {
  region_name: string;
  aws_secret_access_key: string;
  aws_access_key_id: string;
  aws_session_token?: string | null;
};
