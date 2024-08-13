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
  email_address?: string;
  first_name?: string;
  last_name?: string;
  disabled?: boolean;
  disabled_reason?: string;
};
