import type { RequestTypeMetrics } from "./types";

/**
 * Map API action type keys to CCPA/CPRA display labels.
 * The BE returns internal action types; the FE maps them to legal terminology.
 */
export const REQUEST_TYPE_LABELS: Record<string, string> = {
  erasure: "Requests to delete",
  update: "Requests to correct",
  access: "Requests to know",
  consent_opt_out: "Requests to opt-out of sale/sharing",
  limit: "Requests to limit",
};

/**
 * Display order for request types in the metrics table.
 * Types not in this list are appended at the end.
 */
export const REQUEST_TYPE_ORDER = [
  "erasure",
  "update",
  "access",
  "consent_opt_out",
  "limit",
];

/**
 * Request types that the FE always shows even if the BE doesn't return them.
 * These are CCPA-required categories without a current BE equivalent.
 */
export const STATIC_ZERO_REQUEST_TYPES: Record<string, RequestTypeMetrics> = {
  limit: {
    received: 0,
    complied_with: 0,
    denied: 0,
    mean_days_to_respond: null,
    median_days_to_respond: null,
  },
};

/**
 * Column headers for the metrics table, matching the legal disclosure format.
 */
export const METRIC_COLUMNS = [
  { key: "received", label: "Received" },
  { key: "complied_with", label: "Complied (whole or in part)" },
  { key: "denied", label: "Denied" },
  { key: "median_days_to_respond", label: "Median response (days)" },
  { key: "mean_days_to_respond", label: "Mean response (days)" },
] as const;
