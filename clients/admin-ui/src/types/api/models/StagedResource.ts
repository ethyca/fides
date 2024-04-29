/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";

/**
 * Base API model that represents a staged resource, fields common to all types of staged resources
 */
export type StagedResource = {
  urn: string;
  user_assigned_data_categories?: Array<string>;
  name?: string;
  description?: string;
  monitor_config_id?: string;
  updated_at?: string;
  source_modified?: string;
  classifications?: Array<Classification>;
  diff_status?: DiffStatus;
  child_diff_statuses?: Record<string, number>;
};
