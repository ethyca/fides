/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ExecutionLogStatus } from "./ExecutionLogStatus";
import type { TaskRunType } from "./TaskRunType";

/**
 * Response model for task execution logs
 */
export type ExecutionLogResponse = {
  id: string;
  celery_id: string;
  status: ExecutionLogStatus;
  message?: string | null;
  run_type: TaskRunType;
  created_at: string;
  updated_at: string;
};
