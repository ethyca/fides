/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { SaaSConfig_Output } from "./SaaSConfig_Output";
import type { SaaSConfigValidationDetails } from "./SaaSConfigValidationDetails";

/**
 * Response model for validating a SaaS config, which includes both the SaaS config
 * itself (if valid) plus a details object describing any validation errors.
 */
export type ValidateSaaSConfigResponse = {
  saas_config: SaaSConfig_Output;
  validation_details: SaaSConfigValidationDetails;
};
