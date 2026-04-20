import type { PrivacyRequestMetricsResponse } from "./types";

export const MOCK_METRICS: PrivacyRequestMetricsResponse = {
  reporting_period: "January 1, 2025 – December 31, 2025",
  request_types: {
    delete: {
      received: 1243,
      complied_with: 1104,
      denied: 87,
      mean_days_to_respond: 8.3,
      median_days_to_respond: 6,
    },
    correct: {
      received: 312,
      complied_with: 289,
      denied: 14,
      mean_days_to_respond: 5.7,
      median_days_to_respond: 4,
    },
    know: {
      received: 876,
      complied_with: 831,
      denied: 29,
      mean_days_to_respond: 10.1,
      median_days_to_respond: 8,
    },
    opt_out: {
      received: 2104,
      complied_with: 2067,
      denied: 12,
      mean_days_to_respond: 3.2,
      median_days_to_respond: 2,
    },
    limit: {
      received: 418,
      complied_with: 397,
      denied: 8,
      mean_days_to_respond: 4.5,
      median_days_to_respond: 3,
    },
  },
};
