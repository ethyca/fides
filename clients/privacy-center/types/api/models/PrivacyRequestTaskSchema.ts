/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ActionType } from "./ActionType";
import type { ExecutionLogStatus } from "./ExecutionLogStatus";

/**
 * Schema for Privacy Request Tasks, which are individual nodes that are queued
 */
export type PrivacyRequestTaskSchema = {
  status: ExecutionLogStatus;
  id: string;
  collection_address: string;
  created_at: string;
  updated_at: string;
  upstream_tasks: Array<string>;
  downstream_tasks: Array<string>;
  action_type: ActionType;
};
