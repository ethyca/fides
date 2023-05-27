/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type PrivacyRequestNotificationInfo = {
  email_addresses: Array<string>;
  notify_after_failures: number;
};
