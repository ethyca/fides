/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";

/**
 * Pydantic Schema used to represent any StageResource plus extra fields, used only for API responses.
 * It includes all the StagedResource fields, plus all the fields from Database, Schema, Table, and Field,
 * making these optional (since some resources will have them and some won't, depending on the type).
 *
 * The purpose of this model is to not pollute the logic in the existing StagedResource model and its
 * subclasses, since their structure is closely related to the ORM model and its fields, and provide a
 * more extensible way to represent staged resources in API responses (where we may want fields that
 * don't belong to the staged resources table, but are rather obtained from more complex queries, e.g
 * joining against other tables).
 *
 * This model adds the following "extra" fields that are not present on the stagedresources table:
 * - system: the name of the system related to the monitor, if applicable
 * - resource_type: the type of the resource
 */
export type StagedResourceAPIResponse = {
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
  schema_name?: string | null;
  parent_table_urn?: string | null;
  table_name?: string | null;
  data_type?: string | null;
  fields?: Array<string>;
  num_rows?: number | null;
  tables?: Array<string>;
  schemas?: Array<string>;
  resource_type?: string | null;
  system?: string | null;
};
