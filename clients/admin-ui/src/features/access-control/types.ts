export type TimeRange = "24h" | "7d" | "30d";

export interface DataConsumerRequestPoint {
  timestamp: string;
  requests: number;
  violations: number;
}

export interface DataConsumerRequestsResponse {
  violations: number;
  total_requests: number;
  items: DataConsumerRequestPoint[];
}

export interface DataConsumerSummary {
  name: string;
  requests: number;
  violations: number;
}

export interface DataConsumersByViolationsResponse {
  violations: number;
  total_requests: number;
  items: DataConsumerSummary[];
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
  consumer_email: string;
  policy: string;
  policy_description: string;
  dataset: string;
  data_use: string;
  sql_statement: string;
  ai_reason?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface FacetOptionsResponse {
  consumers: string[];
  policies: string[];
  datasets: string[];
  data_uses: string[];
}
