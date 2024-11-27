/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Response schema for a list of staged resources
 */
export type StagedResourceResponse = {
  urn: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  diff_status: string;
  child_diff_statuses: any;
  hidden: boolean;
};
