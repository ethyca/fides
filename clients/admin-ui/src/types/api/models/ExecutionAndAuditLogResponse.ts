/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
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
  status?: string | null;
  updated_at?: string | null;
  user_id?: string | null;
};
