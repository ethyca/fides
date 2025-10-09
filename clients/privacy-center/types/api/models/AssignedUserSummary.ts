/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Minimal user information for manual task assignment list.
 */
export type AssignedUserSummary = {
  /**
   * User ID
   */
  id: string;
  /**
   * Email Address
   */
  email_address?: string | null;
  /**
   * First name
   */
  first_name?: string | null;
  /**
   * Last name
   */
  last_name?: string | null;
};
