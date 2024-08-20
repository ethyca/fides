/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GPPUSApproach } from "./GPPUSApproach";

/**
 * Used to expose the _full_ GPP config in API responses
 */
export type GPPApplicationConfigResponse = {
  us_approach?: GPPUSApproach | null;
  mspa_service_provider_mode?: boolean | null;
  mspa_opt_out_option_mode?: boolean | null;
  mspa_covered_transactions?: boolean | null;
  enable_tcfeu_string?: boolean | null;
  enabled: boolean;
};
