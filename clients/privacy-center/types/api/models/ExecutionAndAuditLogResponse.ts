/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { AuditLogAction } from "./AuditLogAction";
import type { ExecutionLogStatus } from "./ExecutionLogStatus";
import type { FieldsAffectedResponse } from "./FieldsAffectedResponse";

/**
 * Schema for the combined ExecutionLogs and Audit Logs
 * associated with a PrivacyRequest
 */
export type ExecutionAndAuditLogResponse = {
  connection_key?: string | null;
  collection_name?: string | null;
  fields_affected?: Array<FieldsAffectedResponse> | null;
  message?: string | null;
  action_type?: ActionType | null;
  status?: ExecutionLogStatus | AuditLogAction | string | null;
  updated_at?: string | null;
  user_id?: string | null;
};
