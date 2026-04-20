/**
 * Display labels for CCPA/CPRA request types.
 * Keys match the `request_types` keys from the API response.
 */
export const REQUEST_TYPE_LABELS: Record<string, string> = {
  delete: "Requests to delete",
  correct: "Requests to correct",
  know: "Requests to know",
  opt_out: "Requests to opt-out of sale/sharing",
  limit: "Requests to limit",
};

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
