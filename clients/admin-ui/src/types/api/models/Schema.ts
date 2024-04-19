/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ApprovalStatus } from "./ApprovalStatus";
import type { Classification } from "./Classification";
import type { ClassificationStatus } from "./ClassificationStatus";
import type { DiffStatus } from "./DiffStatus";
import type { MonitorStatus } from "./MonitorStatus";

/**
 * Base API model that represents a staged resource, fields common to all types of staged resources
 */
export type Schema = {
  urn: string;
  user_assigned_data_categories?: Array<string>;
  name: string;
  description?: string;
  modified?: string;
  classifications?: Array<Classification>;
  monitor_status?: MonitorStatus;
  approval_status?: ApprovalStatus;
  classification_status?: ClassificationStatus;
  diff_status?: DiffStatus;
  child_diff_statuses?: Array<DiffStatus>;
  tables?: Array<string>;
};
