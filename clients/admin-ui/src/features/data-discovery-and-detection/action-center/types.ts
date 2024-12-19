// TODO: [HJ-334] remove these in favor of autogenerated types from the API
export interface MonitorSummary {
  updates: Record<string, number>;
  property?: string;
  last_monitored: string | number;
  key: string;
  name: string;
  total_updates: number;
  warning?: boolean | string;
}

export interface MonitorSummaryPaginatedResponse {
  items: MonitorSummary[];
  page: number;
  size: number;
  total: number;
}
