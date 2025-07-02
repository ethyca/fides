/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { MonitorTaskType } from "./MonitorTaskType";

/**
 * Response model for monitor tasks
 */
export type MonitorTaskResponse = {
  id: string;
  created_at: string;
  updated_at: string;
  monitor_config_id?: string | null;
  action_type: MonitorTaskType;
  status?: string | null;
  celery_id?: string | null;
  staged_resource_urns?: Array<string>;
};
