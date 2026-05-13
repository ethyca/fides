/* istanbul ignore file */
/* tslint:disable */

import type { ValidationError } from "./ValidationError";

export type HTTPValidationError = {
  detail?: Array<ValidationError>;
};
