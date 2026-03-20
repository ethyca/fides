export type TimeRange = "24h" | "7d" | "30d";

export interface TimeseriesBucket {
  label: string;
  requests: number;
  violations: number;
}

export interface TimeseriesResponse {
  items: TimeseriesBucket[];
}

export interface TopPolicyViolation {
  name: string;
  count: number;
}

export interface AccessControlSummaryResponse {
  violations: number;
  total_requests: number;
  trend: number | null;
  active_consumers: number;
  total_policies: number;
}

export interface ConsumerRequestSummary {
  name: string;
  requests: number;
  violations: number;
}

export interface ConsumerRequestsByConsumerResponse {
  items: ConsumerRequestSummary[];
}

export interface PolicyViolationAggregate {
  policy: string;
  control: string;
  violation_count: number;
  last_violation: string;
}

export interface PolicyViolationLog {
  id: string;
  timestamp: string;
  consumer: string;
  consumer_email?: string;
  policy?: string;
  policy_description?: string;
  control?: string;
  dataset: string;
  data_use?: string;
  sql_statement?: string;
  ai_reason?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface CursorPaginatedViolationLogs {
  items: PolicyViolationLog[];
  next_cursor: string | null;
  size: number;
}

export interface FiltersResponse {
  consumers: string[];
  policies: string[];
  datasets: string[];
  data_uses: string[];
  controls: string[];
}
