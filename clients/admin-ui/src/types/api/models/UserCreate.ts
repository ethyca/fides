/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Data required to create a FidesUser.
 */
export type UserCreate = {
  username: string;
  password?: string;
  email_address: string;
  first_name?: string;
  last_name?: string;
  disabled?: boolean;
};
