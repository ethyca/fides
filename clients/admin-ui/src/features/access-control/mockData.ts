export interface UnresolvedIdentity {
  id: string;
  identifier: string;
  query_count: number;
  datasets: string[];
  last_seen: string;
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
}

export const MOCK_UNRESOLVED_IDENTITIES: UnresolvedIdentity[] = [
  {
    id: "unresolved-1",
    identifier: "marketing-analytics@acme.com",
    query_count: 1247,
    datasets: ["customers", "transactions", "sessions"],
    last_seen: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "unresolved-2",
    identifier: "data-pipeline-prod@acme.iam.gserviceaccount.com",
    query_count: 3891,
    datasets: ["raw_events", "user_profiles", "ml_features", "sessions", "audit_log"],
    last_seen: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
  {
    id: "unresolved-3",
    identifier: "john.doe@acme.com",
    query_count: 142,
    datasets: ["customers"],
    last_seen: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
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
  },
];
