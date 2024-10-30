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
   * Represents the presence of various diff statuses of the staged resource's children. This is computed 'on-demand', i.e. a specific instance method must be invoked to populate the field.
   */
  child_diff_statuses?: Record<string, boolean>;
  database_name?: string | null;
  schema_name: string;
  parent_table_urn: string;
  table_name: string;
  data_type?: string | null;
  sub_field_urns?: Array<string>;
  direct_child_urns?: Array<string>;
  top_level_field_name?: string | null;
  source_data_type?: string | null;
  sub_fields?: Array<Field> | null;
};
