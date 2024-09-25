/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Data required to create a FidesUser.
 */
export type UserCreate = {
  username: string;
  password?: string | null;
  email_address: string;
  first_name?: string | null;
  last_name?: string | null;
  disabled?: boolean;
};
