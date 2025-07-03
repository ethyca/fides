/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExecutionLogResponse } from "./ExecutionLogResponse";
import type { MonitorTaskType } from "./MonitorTaskType";

/**
 * Detailed response model for monitor tasks including execution logs
 */
export type MonitorTaskDetailResponse = {
  id: string;
  created_at: string;
  updated_at: string;
  monitor_config_id?: string | null;
  action_type: MonitorTaskType;
  status?: string | null;
  celery_id?: string | null;
  staged_resource_urns?: Array<string>;
  child_resource_urns?: Array<string>;
  message?: string | null;
  task_arguments?: any;
  execution_logs?: Array<ExecutionLogResponse>;
};
