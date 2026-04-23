import type { PrivacyRequestMetricsResponse } from "./types";

export const MOCK_METRICS: PrivacyRequestMetricsResponse = {
  reporting_period: "January 1, 2025 – December 31, 2025",
  request_types: {
    erasure: {
      received: 1243,
      complied_with: 1104,
      denied: 87,
      mean_days_to_respond: 8.3,
      median_days_to_respond: 6,
    },
    access: {
      received: 876,
      complied_with: 831,
      denied: 29,
      mean_days_to_respond: 10.1,
      median_days_to_respond: 8,
    },
    consent_opt_out: {
      received: 2104,
      complied_with: 2067,
      denied: 12,
      mean_days_to_respond: 3.2,
      median_days_to_respond: 2,
    },
  },
};
