/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Deprecated: This used to be populated and sent to the server by a `config.json` in the UI
 */
export type Consent = {
  data_use: string;
  data_use_description?: string | null;
  opt_in: boolean;
  has_gpc_flag?: boolean;
  conflicts_with_gpc?: boolean;
};
