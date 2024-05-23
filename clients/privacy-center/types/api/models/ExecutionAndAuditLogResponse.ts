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
  connection_key?: string;
  collection_name?: string;
  fields_affected?: Array<FieldsAffectedResponse>;
  message?: string;
  action_type?: ActionType;
  status?: ExecutionLogStatus | AuditLogAction;
  updated_at?: string;
  user_id?: string;
};
