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
  collection_name?: string;
  fields_affected?: Array<FieldsAffectedResponse>;
  message?: string;
  action_type: ActionType;
  status: ExecutionLogStatus;
  updated_at?: string;
  connection_key?: string;
  dataset_name?: string;
};
