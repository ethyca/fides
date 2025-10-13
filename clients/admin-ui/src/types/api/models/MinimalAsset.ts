/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema for a minimal asset response. Used in the privacy experience API.
 * Purposely excludes the page field which can get very large when populated
 * by the web monitor detection process.
 */
export type MinimalAsset = {
  name: string;
  domain?: (string | null);
  data_uses?: Array<string>;
  description?: (string | null);
  duration?: (string | null);
  system_name?: (string | null);
  system_fides_key?: (string | null);
};

