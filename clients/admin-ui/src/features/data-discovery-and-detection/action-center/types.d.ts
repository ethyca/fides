import {
  DatastoreMonitorUpdates,
  MonitorConfigStagedResourcesAggregateRecord,
  WebMonitorUpdates,
} from "~/types/api";
import { PaginatedResponse } from "~/types/query-params";

export interface MonitorAggregatedResults
  extends Omit<MonitorConfigStagedResourcesAggregateRecord, "secrets"> {
  secrets?: { url: string } | null;
}

export type MonitorUpdates = DatastoreMonitorUpdates | WebMonitorUpdates;

export interface MonitorSummaryPaginatedResponse
  extends PaginatedResponse<MonitorAggregatedResults> {}
