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
}

export interface MonitorSummaryPaginatedResponse
  extends PaginatedResponse<MonitorAggregatedResults> {}

export interface MonitorSystemAggregate {
  id: string;
  name: string;
  system_key: string | null; // null when the system is not a known system
  vendor_id: string;
  total_updates: 0;
  data_uses: string[];
  locations: string[];
  domains: string[];
}

export interface MonitorSystemAggregatePaginatedResponse
  extends PaginatedResponse<MonitorSystemAggregate> {}
