/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GPPUSApproach } from "./GPPUSApproach";

export type PrivacyExperienceGPPSettings = {
  us_approach?: GPPUSApproach | null;
  mspa_service_provider_mode?: boolean | null;
  mspa_opt_out_option_mode?: boolean | null;
  mspa_covered_transactions?: boolean | null;
  enable_tcfeu_string?: boolean | null;
  enabled: boolean;
  /**
   * Used by the CMP to determine if the GPP API is required as part of the CMP bundle
   */
  cmp_api_required: boolean;
};
