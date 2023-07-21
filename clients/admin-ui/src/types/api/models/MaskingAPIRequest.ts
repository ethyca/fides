/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { PolicyMaskingSpec } from "./PolicyMaskingSpec";

/**
 * The API Request for masking operations
 */
export type MaskingAPIRequest = {
  values: Array<string>;
  masking_strategy: PolicyMaskingSpec | Array<PolicyMaskingSpec>;
  masking_strategies?: Array<PolicyMaskingSpec>;
};
