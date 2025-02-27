/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";
import type { StagedResourceTypeValue } from "./StagedResourceTypeValue";

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
  /**
   * The data uses associated with the resource
   */
  data_uses?: Array<string> | null;
  user_assigned_data_categories?: Array<string>;
  system_key?: string | null;
  name?: string | null;
  description?: string | null;
  monitor_config_id?: string | null;
  updated_at?: string | null;
  /**
   * The diff status of the staged resource
   */
  diff_status?: DiffStatus | null;
  resource_type?: StagedResourceTypeValue | null;
  source_modified?: string | null;
  classifications?: Array<Classification>;
  /**
   *
   * Represents the presence of various diff statuses of the staged resource's children. This is calculated:
   * - during detection
   * - upon queuing classification
   * - after classification finishes
   * - upon queuing promotion
   * - after promotion finishes
   *
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
  top_level_field_urn?: string | null;
  source_data_type?: string | null;
  sub_fields?: Array<Field> | null;
};
