/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";

/**
 * Base API model that represents a staged resource, fields common to all types of staged resources
 */
export type Field = {
  urn: string;
  user_assigned_data_categories?: Array<string>;
  name?: string;
  description?: string;
  monitor_config_id?: string;
  updated_at?: string;
  source_modified?: string;
  classifications?: Array<Classification>;
  /**
   * The diff status of the staged resource
   */
  diff_status?: DiffStatus;
  /**
   * Stores the aggregate counts of diff statuses of the staged resource's children
   */
  child_diff_statuses?: Record<string, number>;
  database_name: string;
  schema_name: string;
  parent_table: string;
  data_type?: string;
};
