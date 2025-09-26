/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";

/**
 * Pydantic Schema used to represent any StageResource in datastore monitor, used only for API responses.
 */
export type DatastoreStagedResourceAPIResponse = {
  urn: string;
  name?: string | null;
  diff_status?: DiffStatus | null;
  description?: string | null;
  updated_at?: string | null;
  classifications?: Array<Classification>;
  /**
   * User assigned data categories overriding auto assigned classifications
   */
  user_assigned_data_categories?: Array<string> | null;
  data_type?: string | null;
  /**
   * The monitor config that detected this resource
   */
  monitor_config_id: string;
};
