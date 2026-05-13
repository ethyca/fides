/* istanbul ignore file */
/* tslint:disable */

import type { ValidationStatus } from "./ValidationStatus";

/**
 * Validate endpoint response object
 */
export type ValidateResponse = {
  status: ValidationStatus;
  message: string;
};
