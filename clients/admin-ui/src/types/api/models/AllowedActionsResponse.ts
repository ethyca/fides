/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { FieldActionType } from "./FieldActionType";

/**
 * Response for the allowed actions endpoint with strongly-typed action types.
 */
export type AllowedActionsResponse = {
  allowed_actions: Array<FieldActionType>;
  diff_statuses_with_counts: Record<string, number>;
  field_count: number;
};
