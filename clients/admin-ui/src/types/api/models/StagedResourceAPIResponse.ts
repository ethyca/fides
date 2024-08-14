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
 * joning against other tables).
 *
 * This model adds the following "extra" fields that are not present on the stagedresources table:
 * - system: the name of the system related to the monitor, if applicable
 * - resource_type: the type of the resource
 */
export type StagedResourceAPIResponse = {
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
  schema_name?: string;
  parent_table_urn?: string;
  table_name?: string;
  data_type?: string;
  fields?: Array<string>;
  num_rows?: number;
  tables?: Array<string>;
  schemas?: Array<string>;
  resource_type?: string;
  system?: string;
};
