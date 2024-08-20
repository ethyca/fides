/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Describes a Fides registration.
 */
export type Registration = {
  opt_in: boolean;
  analytics_id: string;
  user_email: string | null;
  user_organization: string | null;
};
