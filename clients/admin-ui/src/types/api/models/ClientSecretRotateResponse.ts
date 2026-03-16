/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for secret rotation. Secret is shown exactly once.
 */
export type ClientSecretRotateResponse = {
  client_id: string;
  client_secret: string;
};
