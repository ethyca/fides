/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Summary of a stored SaaS integration version, used for list responses.
 */
export type SaaSConfigVersionResponse = {
  connector_type: string;
  version: string;
  is_custom: boolean;
  created_at: string;
};
