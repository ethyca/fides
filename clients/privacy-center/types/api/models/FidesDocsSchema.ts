/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Fides Child Secrets Schema for API docs
 */
export type FidesDocsSchema = {
  uri: string;
  username: string;
  password: string;
  polling_timeout?: number | null;
  polling_interval?: number | null;
};
