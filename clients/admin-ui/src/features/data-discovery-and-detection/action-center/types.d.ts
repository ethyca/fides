import { MonitorConfigStagedResourcesAggregateRecord } from "~/types/api";
import { PaginatedResponse } from "~/types/query-params";

export interface MonitorAggregatedResults
  extends Omit<MonitorConfigStagedResourcesAggregateRecord, "secrets"> {
  secrets?: { url: string } | null;
}

export interface MonitorSummaryPaginatedResponse
  extends PaginatedResponse<MonitorAggregatedResults> {}
