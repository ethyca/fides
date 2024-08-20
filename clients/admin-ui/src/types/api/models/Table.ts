/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";

export type Table = {
  urn: string;
  user_assigned_data_categories?: Array<string>;
  name?: string | null;
  description?: string | null;
  monitor_config_id?: string | null;
  updated_at?: string | null;
  source_modified?: string | null;
  classifications?: Array<Classification>;
  /**
   * The diff status of the staged resource
   */
  diff_status?: DiffStatus | null;
  /**
   * Represents the aggregate counts of diff statuses of the staged resource's children. This is computed 'on-demand', i.e. a specific instance method must be invoked to populate the field.
   */
  child_diff_statuses?: Record<string, number>;
  database_name?: string | null;
  schema_name: string;
  parent_schema: string;
  fields?: Array<string>;
  num_rows?: number | null;
};
