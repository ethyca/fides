/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Extended UserResponse schema to allow specifying if password login is enabled.
 */
export type UserResponseExtended = {
  id: string;
  username: string;
  created_at: string;
  email_address: string | null;
  first_name?: string | null;
  last_name?: string | null;
  disabled?: boolean | null;
  disabled_reason?: string | null;
  /**
   * Whether password login is enabled for the user.
   */
  password_login_enabled?: boolean | null;
};
