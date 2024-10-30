/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { ExecutionLogStatus } from "./ExecutionLogStatus";
import type { FieldsAffectedResponse } from "./FieldsAffectedResponse";

/**
 * Schema for the detailed ExecutionLogs when accessed directly
 */
export type ExecutionLogDetailResponse = {
  status: ExecutionLogStatus;
  collection_name?: string | null;
  fields_affected?: Array<FieldsAffectedResponse> | null;
  message?: string | null;
  action_type: ActionType;
  updated_at?: string | null;
  connection_key?: string | null;
  dataset_name?: string | null;
};
