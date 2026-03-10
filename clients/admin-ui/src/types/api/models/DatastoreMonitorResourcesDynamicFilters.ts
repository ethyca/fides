/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConfidenceBucket } from "./ConfidenceBucket";

export type DatastoreMonitorResourcesDynamicFilters = {
  diff_status?: Array<string> | null;
  data_category?: Array<string> | null;
  confidence_bucket?: Array<ConfidenceBucket> | null;
};
