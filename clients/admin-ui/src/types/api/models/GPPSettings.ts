/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GPPUSApproach } from "./GPPUSApproach";

/**
 * Configuration settings for GPP
 */
export type GPPSettings = {
  enabled?: boolean;
  /**
   * National ('national') or state-by-state ('state') approach.
   */
  us_approach?: GPPUSApproach;
  /**
   * Whether MSPA service provider mode is enabled
   */
  mspa_service_provider_mode?: boolean;
  /**
   * Whether MSPA opt out option mode is enabled
   */
  mspa_opt_out_option_mode?: boolean;
  /**
   * Whether all transactions are MSPA covered
   */
  mspa_covered_transactions?: boolean;
  /**
   * Whether TC string should be included as a section in GPP
   */
  enable_tc_string?: boolean;
};
