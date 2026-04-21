export interface UnresolvedIdentity {
  id: string;
  identifier: string;
  query_count: number;
  datasets: string[];
  last_seen: string;
  inferred_type: string;
  inferred_purpose: string;
  inference_confidence: number;
}

export type FindingSeverity = "critical" | "high" | "medium" | "low";

export interface ViolationCard {
  id: string;
  consumer_id: string;
  consumer_name: string;
  purpose: string;
  tables: string[];
  query_count: number;
  last_seen: string;
  severity: FindingSeverity;
}

export interface GapCard {
  id: string;
  consumer_id: string | null;
  consumer_name: string;
  dataset: string;
  tables: string[];
  query_count: number;
  last_seen: string;
  severity: FindingSeverity;
  inferred_purpose: string;
  inference_confidence: number;
}

export const MOCK_UNRESOLVED_IDENTITIES: UnresolvedIdentity[] = [
  {
    id: "unresolved-1",
    identifier: "marketing-analytics@acme.com",
    query_count: 1247,
    datasets: ["customers", "transactions", "sessions"],
    last_seen: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    inferred_type: "Marketing team",
    inferred_purpose: "Campaign targeting",
    inference_confidence: 87,
  },
  {
    id: "unresolved-2",
    identifier: "data-pipeline-prod@acme.iam.gserviceaccount.com",
    query_count: 3891,
    datasets: ["raw_events", "user_profiles", "ml_features", "sessions", "audit_log"],
    last_seen: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    inferred_type: "ETL service",
    inferred_purpose: "Analytics",
    inference_confidence: 94,
  },
  {
    id: "unresolved-3",
    identifier: "john.doe@acme.com",
    query_count: 142,
    datasets: ["customers"],
    last_seen: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    inferred_type: "Individual user",
    inferred_purpose: "Customer support",
    inference_confidence: 62,
  },
  {
    id: "unresolved-4",
    identifier: "analytics-cron@acme.iam.gserviceaccount.com",
    query_count: 5210,
    datasets: ["raw_events", "sessions", "page_views"],
    last_seen: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    inferred_type: "Scheduled job",
    inferred_purpose: "Analytics",
    inference_confidence: 91,
  },
  {
    id: "unresolved-5",
    identifier: "ml-training@acme.iam.gserviceaccount.com",
    query_count: 8430,
    datasets: ["user_profiles", "behavior_events", "ml_features", "churn_predictions"],
    last_seen: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    inferred_type: "ML pipeline",
    inferred_purpose: "Model training",
    inference_confidence: 96,
  },
  {
    id: "unresolved-6",
    identifier: "sarah.chen@acme.com",
    query_count: 67,
    datasets: ["customers", "support_cases"],
    last_seen: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
    inferred_type: "Individual user",
    inferred_purpose: "Ticket resolution",
    inference_confidence: 74,
  },
  {
    id: "unresolved-7",
    identifier: "export-service@acme.iam.gserviceaccount.com",
    query_count: 2100,
    datasets: ["payment_transactions", "invoices", "subscription_events"],
    last_seen: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    inferred_type: "ETL service",
    inferred_purpose: "Financial reporting",
    inference_confidence: 88,
  },
];

export const MOCK_VIOLATION_CARDS: ViolationCard[] = [
  {
    id: "violation-1",
    consumer_id: "1",
    consumer_name: "Marketing Analytics",
    purpose: "Campaign targeting",
    tables: ["payment_transactions", "user_sessions", "identity_documents"],
    query_count: 847,
    last_seen: "2026-03-30T09:14:00Z",
    severity: "critical",
  },
  {
    id: "violation-2",
    consumer_id: "3",
    consumer_name: "Growth Engineering",
    purpose: "Campaign targeting",
    tables: ["user_sessions", "ad_impressions"],
    query_count: 214,
    last_seen: "2026-03-29T22:00:00Z",
    severity: "high",
  },
  {
    id: "violation-3",
    consumer_id: "1",
    consumer_name: "Marketing Analytics",
    purpose: "Audience segmentation",
    tables: ["user_profiles", "behavior_events"],
    query_count: 391,
    last_seen: "2026-03-29T17:42:00Z",
    severity: "high",
  },
  {
    id: "violation-4",
    consumer_id: "2",
    consumer_name: "CS Support",
    purpose: "Ticket resolution",
    tables: ["customer_pii", "support_cases"],
    query_count: 203,
    last_seen: "2026-03-28T11:05:00Z",
    severity: "medium",
  },
  {
    id: "violation-5",
    consumer_id: "4",
    consumer_name: "Data Science",
    purpose: "Ticket resolution",
    tables: ["support_cases", "customer_feedback"],
    query_count: 76,
    last_seen: "2026-03-27T15:30:00Z",
    severity: "low",
  },
  {
    id: "violation-6",
    consumer_id: "5",
    consumer_name: "Revenue Operations",
    purpose: "Financial reporting",
    tables: ["payment_transactions", "subscription_events"],
    query_count: 432,
    last_seen: "2026-03-30T07:20:00Z",
    severity: "high",
  },
  {
    id: "violation-7",
    consumer_id: "1",
    consumer_name: "Marketing Analytics",
    purpose: "Financial reporting",
    tables: ["payment_transactions", "invoices"],
    query_count: 156,
    last_seen: "2026-03-29T14:00:00Z",
    severity: "medium",
  },
  {
    id: "violation-8",
    consumer_id: "6",
    consumer_name: "Product Analytics",
    purpose: "User profiling",
    tables: ["user_profiles", "behavioral_signals", "device_fingerprints"],
    query_count: 1203,
    last_seen: "2026-03-30T11:45:00Z",
    severity: "critical",
  },
  {
    id: "violation-9",
    consumer_id: "3",
    consumer_name: "Growth Engineering",
    purpose: "User profiling",
    tables: ["behavioral_signals", "conversion_events"],
    query_count: 567,
    last_seen: "2026-03-29T19:30:00Z",
    severity: "high",
  },
  {
    id: "violation-10",
    consumer_id: "7",
    consumer_name: "Fraud Detection",
    purpose: "Identity verification",
    tables: ["identity_documents", "authentication_logs"],
    query_count: 89,
    last_seen: "2026-03-28T08:15:00Z",
    severity: "low",
  },
];

export const MOCK_GAP_CARDS: GapCard[] = [
  {
    id: "gap-1",
    consumer_id: "1",
    consumer_name: "Marketing Analytics",
    dataset: "Snowflake — ml_features",
    tables: ["churn_predictions", "ltv_scores"],
    query_count: 312,
    last_seen: "2026-03-30T14:22:00Z",
    severity: "high",
    inferred_purpose: "Customer Analytics",
    inference_confidence: 91,
  },
  {
    id: "gap-2",
    consumer_id: "1",
    consumer_name: "Marketing Analytics",
    dataset: "BigQuery — ab_test_results",
    tables: ["experiment_assignments", "conversion_events"],
    query_count: 189,
    last_seen: "2026-03-29T10:15:00Z",
    severity: "medium",
    inferred_purpose: "Feature Adoption Tracking",
    inference_confidence: 78,
  },
  {
    id: "gap-3",
    consumer_id: "2",
    consumer_name: "CS Support",
    dataset: "BigQuery — raw_events",
    tables: ["click_stream", "page_views"],
    query_count: 88,
    last_seen: "2026-03-27T09:31:00Z",
    severity: "low",
    inferred_purpose: "Ticket resolution",
    inference_confidence: 68,
  },
  {
    id: "gap-4",
    consumer_id: null,
    consumer_name: "Unknown (data-pipeline-prod@acme.iam)",
    dataset: "Snowflake — user_profiles",
    tables: ["user_profiles", "identity_graph"],
    query_count: 1420,
    last_seen: "2026-03-30T16:00:00Z",
    severity: "high",
    inferred_purpose: "Analytics",
    inference_confidence: 83,
  },
  {
    id: "gap-5",
    consumer_id: "4",
    consumer_name: "Data Science",
    dataset: "Snowflake — churn_predictions",
    tables: ["churn_predictions", "ltv_scores", "feature_store"],
    query_count: 890,
    last_seen: "2026-03-30T10:00:00Z",
    severity: "medium",
    inferred_purpose: "Model training",
    inference_confidence: 92,
  },
  {
    id: "gap-6",
    consumer_id: "5",
    consumer_name: "Revenue Operations",
    dataset: "BigQuery — subscription_events",
    tables: ["subscription_events", "mrr_snapshots"],
    query_count: 234,
    last_seen: "2026-03-29T16:45:00Z",
    severity: "medium",
    inferred_purpose: "Financial reporting",
    inference_confidence: 86,
  },
  {
    id: "gap-7",
    consumer_id: null,
    consumer_name: "Unknown (ml-training@acme.iam)",
    dataset: "Snowflake — behavioral_signals",
    tables: ["behavioral_signals", "device_fingerprints"],
    query_count: 3200,
    last_seen: "2026-03-30T14:30:00Z",
    severity: "critical",
    inferred_purpose: "Model training",
    inference_confidence: 95,
  },
  {
    id: "gap-8",
    consumer_id: "6",
    consumer_name: "Product Analytics",
    dataset: "BigQuery — feature_flags",
    tables: ["feature_flags", "experiment_results"],
    query_count: 156,
    last_seen: "2026-03-28T12:00:00Z",
    severity: "low",
    inferred_purpose: "Feature Adoption Tracking",
    inference_confidence: 89,
  },
];

export interface QueryLogEntry {
  id: string;
  consumer_id: string;
  consumer_name: string;
  policy: string;
  table_accessed: string;
  query_type: "SELECT" | "INSERT" | "UPDATE" | "DELETE" | "COPY";
  rows_accessed: number;
  timestamp: string;
  inferred_purpose: string;
  inference_confidence: number;
  matches_policy: boolean;
}

const h = (hoursAgo: number) =>
  new Date(Date.now() - hoursAgo * 60 * 60 * 1000).toISOString();

export const MOCK_QUERY_LOG: QueryLogEntry[] = [
  { id: "q1", consumer_id: "1", consumer_name: "Marketing Analytics", policy: "Campaign targeting", table_accessed: "payment_transactions", query_type: "SELECT", rows_accessed: 48200, timestamp: h(1), inferred_purpose: "Fraud detection", inference_confidence: 82, matches_policy: false },
  { id: "q2", consumer_id: "1", consumer_name: "Marketing Analytics", policy: "Campaign targeting", table_accessed: "user_sessions", query_type: "SELECT", rows_accessed: 124000, timestamp: h(1.5), inferred_purpose: "Campaign targeting", inference_confidence: 95, matches_policy: true },
  { id: "q3", consumer_id: "1", consumer_name: "Marketing Analytics", policy: "Campaign targeting", table_accessed: "identity_documents", query_type: "SELECT", rows_accessed: 8400, timestamp: h(3), inferred_purpose: "Identity verification", inference_confidence: 88, matches_policy: false },
  { id: "q4", consumer_id: "3", consumer_name: "Growth Engineering", policy: "Campaign targeting", table_accessed: "user_sessions", query_type: "SELECT", rows_accessed: 67000, timestamp: h(5), inferred_purpose: "Campaign targeting", inference_confidence: 91, matches_policy: true },
  { id: "q5", consumer_id: "3", consumer_name: "Growth Engineering", policy: "Campaign targeting", table_accessed: "ad_impressions", query_type: "SELECT", rows_accessed: 31500, timestamp: h(8), inferred_purpose: "Campaign targeting", inference_confidence: 96, matches_policy: true },
  { id: "q6", consumer_id: "1", consumer_name: "Marketing Analytics", policy: "Campaign targeting", table_accessed: "payment_transactions", query_type: "SELECT", rows_accessed: 52100, timestamp: h(12), inferred_purpose: "Fraud detection", inference_confidence: 79, matches_policy: false },
  { id: "q7", consumer_id: "1", consumer_name: "Marketing Analytics", policy: "Campaign targeting", table_accessed: "user_sessions", query_type: "COPY", rows_accessed: 240000, timestamp: h(18), inferred_purpose: "Campaign targeting", inference_confidence: 93, matches_policy: true },
  { id: "q8", consumer_id: "3", consumer_name: "Growth Engineering", policy: "Campaign targeting", table_accessed: "user_sessions", query_type: "SELECT", rows_accessed: 89000, timestamp: h(24), inferred_purpose: "Campaign targeting", inference_confidence: 90, matches_policy: true },
  { id: "q9", consumer_id: "1", consumer_name: "Marketing Analytics", policy: "Audience segmentation", table_accessed: "user_profiles", query_type: "SELECT", rows_accessed: 95000, timestamp: h(2), inferred_purpose: "Audience segmentation", inference_confidence: 97, matches_policy: true },
  { id: "q10", consumer_id: "1", consumer_name: "Marketing Analytics", policy: "Audience segmentation", table_accessed: "behavior_events", query_type: "SELECT", rows_accessed: 310000, timestamp: h(6), inferred_purpose: "Audience segmentation", inference_confidence: 94, matches_policy: true },
  { id: "q11", consumer_id: "1", consumer_name: "Marketing Analytics", policy: "Audience segmentation", table_accessed: "user_profiles", query_type: "SELECT", rows_accessed: 88000, timestamp: h(14), inferred_purpose: "Customer Analytics", inference_confidence: 72, matches_policy: false },
  { id: "q12", consumer_id: "2", consumer_name: "CS Support", policy: "Ticket resolution", table_accessed: "customer_pii", query_type: "SELECT", rows_accessed: 2400, timestamp: h(4), inferred_purpose: "Ticket resolution", inference_confidence: 98, matches_policy: true },
  { id: "q13", consumer_id: "2", consumer_name: "CS Support", policy: "Ticket resolution", table_accessed: "support_cases", query_type: "SELECT", rows_accessed: 1800, timestamp: h(10), inferred_purpose: "Ticket resolution", inference_confidence: 99, matches_policy: true },
  { id: "q14", consumer_id: "4", consumer_name: "Data Science", policy: "Ticket resolution", table_accessed: "support_cases", query_type: "SELECT", rows_accessed: 45000, timestamp: h(30), inferred_purpose: "Model training", inference_confidence: 85, matches_policy: false },
  { id: "q15", consumer_id: "4", consumer_name: "Data Science", policy: "Ticket resolution", table_accessed: "customer_feedback", query_type: "SELECT", rows_accessed: 12000, timestamp: h(48), inferred_purpose: "Sentiment analysis", inference_confidence: 81, matches_policy: false },
];
