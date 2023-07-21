/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Overrides basic IdentityTypes to add cookie_ids
 */
export type ExtendedIdentityTypes = {
  email: boolean;
  phone_number: boolean;
  cookie_ids?: Array<string>;
};
