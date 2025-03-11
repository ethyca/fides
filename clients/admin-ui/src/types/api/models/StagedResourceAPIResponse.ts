/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";
import type { StagedResourceTypeValue } from "./StagedResourceTypeValue";

/**
 * Pydantic Schema used to represent any StageResource plus extra fields, used only for API responses.
 * It includes all the StagedResource fields, plus all the fields from Database, Schema, Table, and Field,
 * making these optional (since some resources will have them and some won't, depending on the type).
 *
 * The purpose of this model is to not pollute the logic in the existing StagedResource model and its
 * subclasses, since their structure is closely related to the ORM model and its fields, and provide a
 * more extensible way to represent staged resources in API responses (where we may want fields that
 * don't belong to the stagedresources table, but are rather obtained from more complex queries, e.g
 * joining against other tables).
 *
 * This model adds the following "extra" fields that are not present on the stagedresources table:
 * - system: the name of the system related to the monitor, if applicable
 */
export type StagedResourceAPIResponse = {
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
  domain?: string | null;
  /**
   * The parent(s) of the asset, i.e. from where the asset was identified
   */
  parent?: Array<string>;
  parent_domain?: string | null;
  /**
   * The location(s) from which the asset was discovered
   */
  locations?: Array<string>;
  /**
   * Whether the asset was discovered with consent
   */
  with_consent?: boolean;
  /**
   * The Compass Vendor ID associated with the asset
   */
  vendor_id?: string | null;
  /**
   * The Fides System ID associated with the asset
   */
  system_id?: string | null;
  database_name?: string | null;
  schema_name?: string | null;
  parent_table_urn?: string | null;
  table_name?: string | null;
  data_type?: string | null;
  fields?: Array<string>;
  num_rows?: number | null;
  tables?: Array<string>;
  schemas?: Array<string>;
  system?: string | null;
};
