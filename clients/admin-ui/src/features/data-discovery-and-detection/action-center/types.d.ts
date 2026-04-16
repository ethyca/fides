import {
  DatastoreMonitorUpdates,
  MonitorConfigStagedResourcesAggregateRecord,
  WebMonitorUpdates,
} from "~/types/api";
import { APIMonitorType } from "~/types/api/models/APIMonitorType";
import { InfrastructureMonitorUpdates } from "~/types/api/models/InfrastructureMonitorUpdates";
import { PaginatedResponse } from "~/types/query-params";

export interface MonitorAggregatedResults
  extends Omit<MonitorConfigStagedResourcesAggregateRecord, "secrets"> {
  secrets?: { url: string } | null;
  monitorType: APIMonitorType;
  isTestMonitor: boolean;
}

export type MonitorUpdates =
  | DatastoreMonitorUpdates
  | WebMonitorUpdates
  | InfrastructureMonitorUpdates;

export interface MonitorSummaryPaginatedResponse
  extends PaginatedResponse<MonitorAggregatedResults> {}

export type DatastorePageSettings = {
  showIgnored: boolean;
  showApproved: boolean;
};
