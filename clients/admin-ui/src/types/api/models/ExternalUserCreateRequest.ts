/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Data required to create an external respondent user
 */
export type ExternalUserCreateRequest = {
  username: string;
  email_address: string;
  first_name?: string | null;
  last_name?: string | null;
};
