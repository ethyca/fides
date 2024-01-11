/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { fidesplus__config__gpp_settings__GPPUSApproach } from "./fidesplus__config__gpp_settings__GPPUSApproach";

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type GPPApplicationConfig = {
  us_approach?: fidesplus__config__gpp_settings__GPPUSApproach;
  mspa_service_provider_mode?: boolean;
  mspa_opt_out_option_mode?: boolean;
  mspa_covered_transactions?: boolean;
};
