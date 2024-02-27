/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Similar to UserCreate except we do not need the extra validation on
 * username and password.
 */
export type UserLogin = {
  username: string;
  password: string;
};
