/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DiffStatus } from "./DiffStatus";
import type { StagedResourceTypeValue } from "./StagedResourceTypeValue";

/**
 * Base API model that represents a staged resource, fields common to all types of staged resources
 */
export type StagedResource = {
  urn: string;
  user_assigned_data_categories?: Array<string> | null;
  /**
   * User assigned data uses overriding auto assigned data uses
   */
  user_assigned_data_uses?: Array<string> | null;
  user_assigned_system_key?: string | null;
  name?: string | null;
  system_key?: string | null;
  description?: string | null;
  monitor_config_id?: string | null;
  updated_at?: string | null;
  /**
   * The diff status of the staged resource
   */
  diff_status?: DiffStatus | null;
  resource_type?: StagedResourceTypeValue | null;
  /**
   * The data uses associated with the staged resource
   */
  data_uses?: Array<string> | null;
};
