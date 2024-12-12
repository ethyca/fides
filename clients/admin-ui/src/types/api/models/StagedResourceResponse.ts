/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for a list of staged resources
 */
export type StagedResourceResponse = {
  urn: string;
  name: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  diff_status: string | null;
  child_diff_statuses: any;
  hidden: boolean;
  monitor_config_id: string | null;
  resource_type: string | null;
};
