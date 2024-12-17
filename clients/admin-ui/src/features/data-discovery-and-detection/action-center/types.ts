export interface MonitorSummary {
  updates: Record<string, number>;
  hostname?: string;
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
