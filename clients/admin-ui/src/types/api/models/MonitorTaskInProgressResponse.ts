/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for in-progress monitor tasks in the Action Center.
 */
export type MonitorTaskInProgressResponse = {
  id: string;
  monitor_name: string;
  task_type: string;
  last_updated: string;
  status: string;
  staged_resource_urns?: Array<string> | null;
  connection_type?: string | null;
  monitor_config_id: string;
  message?: string | null;
};
