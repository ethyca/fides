/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { GPPSections } from "./GPPSections";
import type { GPPUSApproach } from "./GPPUSApproach";

/**
 * Configuration settings for GPP
 */
export type GPPSettings = {
  enabled?: boolean;
  regions?: Array<GPPSections>;
  /**
   * National ('national') or state-by-state ('state') approach. Only required if regions includes US.
   */
  us_approach?: GPPUSApproach;
  /**
   * List of US states. Only required if using a state-by-state approach.
   */
  us_states?: Array<string>;
};
