/**
 * Map API action type keys to CCPA/CPRA display labels.
 * The BE returns internal action types; the FE maps them to legal terminology.
 */
export const REQUEST_TYPE_LABELS: Record<string, string> = {
  erasure: "Requests to delete",
  access: "Requests to know",
  consent_opt_out: "Requests to opt-out of sale/sharing",
};

/**
 * Display order for request types in the metrics table.
 * Types not in this list are appended at the end.
 */
export const REQUEST_TYPE_ORDER = [
  "erasure",
  "access",
  "consent_opt_out",
];

/**
 * Column headers for the metrics table, matching the legal disclosure format.
 */
export const METRIC_COLUMNS = [
  { key: "received", label: "Received" },
  { key: "complied_with", label: "Complied with (whole or in part)" },
  { key: "denied", label: "Denied" },
  { key: "median_days_to_respond", label: "Median days to respond" },
  { key: "mean_days_to_respond", label: "Mean days to respond" },
] as const;
