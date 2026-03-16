/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for an OAuth client. Never includes the client secret.
 */
export type ClientResponse = {
  client_id: string;
  name?: string | null;
  description?: string | null;
  scopes: Array<string>;
};
