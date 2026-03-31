/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { APIMonitorType } from "./APIMonitorType";
import type { ApprovalProgress } from "./ApprovalProgress";
import type { StatusCounts } from "./StatusCounts";
import type { TopClassifications } from "./TopClassifications";
import type { VendorCounts } from "./VendorCounts";
import type { WebResourceTypeCounts } from "./WebResourceTypeCounts";

/**
 * Cross-monitor aggregate statistics. Same shape for all monitor types.
 */
export type AggregateStatisticsResponse = {
  monitor_type: APIMonitorType;
  last_updated?: string | null;
  total_monitors?: number;
  total_resources?: number;
  status_counts?: StatusCounts;
  approval_progress?: ApprovalProgress;
  top_classifications?: TopClassifications;
  vendor_counts?: VendorCounts | null;
  resource_type_counts?: WebResourceTypeCounts | null;
};
