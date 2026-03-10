/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for a user assigned as a monitor steward.
 */
export type MonitorStewardUserResponse = {
  id: string;
  username: string;
  email_address?: string | null;
  first_name?: string | null;
  last_name?: string | null;
};
