/** Metrics for a single request type (e.g. "Requests to Delete") */
export interface RequestTypeMetrics {
  received: number;
  complied_with: number;
  denied: number;
  mean_days_to_respond: number | null;
  median_days_to_respond: number | null;
}

/**
 * Response shape for the privacy request metrics endpoint.
 * Modeled after CCPA/CPRA annual metrics disclosure requirements
 * (California 11 CCR 7102).
 */
export interface PrivacyRequestMetricsResponse {
  reporting_period: string;
  request_types: Record<string, RequestTypeMetrics>;
}
