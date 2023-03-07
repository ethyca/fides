/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for consent.
 */
export type Consent = {
  data_use: string;
  data_use_description?: string;
  opt_in: boolean;
  has_gpc_flag?: boolean;
  conflicts_with_gpc?: boolean;
};
