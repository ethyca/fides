/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Location field configuration that extends the useful parts of CustomPrivacyRequestField
 */
export type LocationIdentityField = {
  label: string;
  required?: boolean | null;
  default_value?: string | null;
  query_param_key?: string | null;
  ip_geolocation_hint?: boolean | null;
};
