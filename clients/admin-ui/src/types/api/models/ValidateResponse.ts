/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ValidationStatus } from "./ValidationStatus";

/**
 * Validate endpoint response object
 */
export type ValidateResponse = {
  status: ValidationStatus;
  message: string;
};
