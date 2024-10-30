/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { AWSConfig } from "./AWSConfig";
import type { BigQueryConfig } from "./BigQueryConfig";
import type { OktaConfig } from "./OktaConfig";
import type { ValidationTarget } from "./ValidationTarget";

/**
 * Validate endpoint request object
 */
export type ValidateRequest = {
  config: AWSConfig | BigQueryConfig | OktaConfig;
  target: ValidationTarget;
};
