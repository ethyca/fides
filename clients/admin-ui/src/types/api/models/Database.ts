/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { Classification } from "./Classification";
import type { DiffStatus } from "./DiffStatus";
import type { MonitorStatus } from "./MonitorStatus";

/**
 * Base API model that represents a staged resource, fields common to all types of staged resources
 */
export type Database = {
  urn: string;
  user_assigned_data_categories?: Array<string>;
  name: string;
  description?: string;
  monitor_config_id: string;
  modified?: string;
  classifications?: Array<Classification>;
  monitor_status?: MonitorStatus;
  diff_status?: DiffStatus;
  child_diff_statuses?: Array<DiffStatus>;
  schemas?: Array<string>;
};
