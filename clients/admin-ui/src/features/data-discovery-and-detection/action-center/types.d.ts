import { PaginatedResponse } from "~/types/common/PaginationQueryParams";

// TODO: [HJ-334] remove these in favor of autogenerated types from the API
export interface MonitorAggregatedResults {
  updates: Record<string, number>;
  property?: string; // this is a guess, it doesn't exist yet in the API
  last_monitored: string | number;
  key: string;
  name: string;
  total_updates: number;
  warning?: boolean | string;
  secrets?: { url: string };
}

export interface MonitorSummaryPaginatedResponse
  extends PaginatedResponse<MonitorAggregatedResults> {}
