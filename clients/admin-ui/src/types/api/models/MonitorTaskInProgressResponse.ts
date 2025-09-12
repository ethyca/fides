/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for in-progress monitor tasks in the Action Center.
 */
export type MonitorTaskInProgressResponse = {
  id: string;
  created_at: string;
  updated_at: string;
  monitor_config_id?: string | null;
  monitor_name?: string | null;
  action_type: string;
  status: string;
  message?: string | null;
  staged_resource_urns?: Array<string> | null;
  connection_type?: string | null;
  connection_name?: string | null;
};
