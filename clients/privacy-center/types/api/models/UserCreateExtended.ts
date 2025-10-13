/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Extended UserCreate schema to allow specifying if password login is enabled.
 */
export type UserCreateExtended = {
  username: string;
  password?: string | null;
  email_address: string;
  first_name?: string | null;
  last_name?: string | null;
  disabled?: boolean;
  /**
   * Whether password login is enabled for the user.
   */
  password_login_enabled?: boolean | null;
};
