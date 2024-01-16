/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GPPUSApproach } from "./GPPUSApproach";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type GPPApplicationConfig = {
  us_approach?: GPPUSApproach;
  mspa_service_provider_mode?: boolean;
  mspa_opt_out_option_mode?: boolean;
  mspa_covered_transactions?: boolean;
  enable_tc_string?: boolean;
};
