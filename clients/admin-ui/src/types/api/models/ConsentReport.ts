/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { IdentityBase } from "./IdentityBase";

/**
 * Schema for reporting Consent requests.
 */
export type ConsentReport = {
  data_use: string;
  data_use_description?: string;
  opt_in: boolean;
  has_gpc_flag?: boolean;
  conflicts_with_gpc?: boolean;
  identity: IdentityBase;
  created_at: string;
  updated_at: string;
};
