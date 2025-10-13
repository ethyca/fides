/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ConfidenceScoreRange } from './ConfidenceScoreRange';

export type DatastoreMonitorResourcesDynamicFilters = {
  diff_status?: (Array<string> | null);
  data_category?: (Array<string> | null);
  confidence_score?: (Array<ConfidenceScoreRange> | null);
};

