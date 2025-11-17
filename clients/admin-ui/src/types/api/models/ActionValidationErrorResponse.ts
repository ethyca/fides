/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DiffStatus } from "./DiffStatus";
import type { FieldActionType } from "./FieldActionType";

/**
 * Structured error response when an action cannot be performed due to invalid diff_statuses.
 */
export type ActionValidationErrorResponse = {
  action_type: FieldActionType;
  disallowed_statuses_with_counts: Record<string, number>;
  allowed_statuses: Array<DiffStatus>;
  message: string;
};
