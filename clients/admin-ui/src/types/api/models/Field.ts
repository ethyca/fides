/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";

/**
 * The Field model is also used to represent "sub-fields" that are nested under a
 * top-level field in a data source.
 *
 * In these cases, the `name` attribute on the Field should be the full "path"
 * to the sub-field, minus the name of the top-level field.
 *
 * The top-level field name for a given sub-field is stored in its own attribute,
 * which is only populated if the Field is a sub-field.
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
   * Represents the aggregate counts of diff statuses of the staged resource's children. This is computed 'on-demand', i.e. a specific instance method must be invoked to populate the field.
   */
  child_diff_statuses?: Record<string, number>;
  database_name?: string;
  schema_name: string;
  parent_table_urn: string;
  table_name: string;
  data_type?: string;
  sub_field_urns?: Array<string>;
  direct_child_urns?: Array<string>;
  top_level_field_name?: string;
  source_data_type?: string;
};
