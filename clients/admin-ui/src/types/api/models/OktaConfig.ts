/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * The model for the connection config for Okta
 */
export type OktaConfig = {
  orgUrl: string;
  clientId: string;
  privateKey: string;
  scopes?: Array<string>;
};
