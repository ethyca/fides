import {
  DatastoreMonitorUpdates,
  MonitorConfigStagedResourcesAggregateRecord,
  WebMonitorUpdates,
} from "~/types/api";
import { PaginatedResponse } from "~/types/query-params";

import { MONITOR_TYPES } from "./utils/getMonitorType";

export interface MonitorAggregatedResults
  extends Omit<MonitorConfigStagedResourcesAggregateRecord, "secrets"> {
  secrets?: { url: string } | null;
  monitorType: MONITOR_TYPES;
  isTestMonitor: boolean;
}

export type MonitorUpdates = DatastoreMonitorUpdates | WebMonitorUpdates;

export interface MonitorSummaryPaginatedResponse
  extends PaginatedResponse<MonitorAggregatedResults> {}
