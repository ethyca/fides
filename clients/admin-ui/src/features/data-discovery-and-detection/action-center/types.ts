export interface MonitorSummary {
  asset_counts: {
    type: string;
    count: number;
  }[];
  hostname: string;
  last_monitored: string | number;
  monitor_config_id: string;
  name: string;
  total_assets: number;
  warning?: boolean | string;
}

export interface MonitorSummaryPaginatedResponse {
  items: MonitorSummary[];
  page: number;
  size: number;
  total: number;
}
