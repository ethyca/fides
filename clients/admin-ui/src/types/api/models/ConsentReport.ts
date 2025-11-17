/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fides__api__schemas__redis_cache__Identity } from "./fides__api__schemas__redis_cache__Identity";

/**
 * Keeps record of each of the preferences that have been recorded via ConsentReporting endpoints.
 */
export type ConsentReport = {
  data_use: string;
  data_use_description?: string | null;
  opt_in: boolean;
  has_gpc_flag?: boolean;
  conflicts_with_gpc?: boolean;
  id: string;
  identity: fides__api__schemas__redis_cache__Identity;
  created_at: string;
  updated_at: string;
};
