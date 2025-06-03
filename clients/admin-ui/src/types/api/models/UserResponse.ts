/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response after requesting a User
 */
export type UserResponse = {
  id: string;
  username: string;
  created_at: string;
  email_address: string | null;
  first_name?: string | null;
  last_name?: string | null;
  disabled?: boolean | null;
  disabled_reason?: string | null;
};
