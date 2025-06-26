import { MonitorConfigStagedResourcesAggregateRecord } from "~/types/api";
import { PaginatedResponse } from "~/types/common/PaginationQueryParams";

export interface MonitorAggregatedResults
  extends Omit<MonitorConfigStagedResourcesAggregateRecord, "secrets"> {
  secrets?: { url: string } | null;
}

export interface MonitorSummaryPaginatedResponse
  extends PaginatedResponse<MonitorAggregatedResults> {}
