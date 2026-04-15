import type {
  ConsumerViolation,
  MockDataConsumer,
  PolicyGap,
  PolicyViolationGroup,
} from "./types";

export const MOCK_DATA_CONSUMERS: MockDataConsumer[] = [
  {
    id: "1",
    name: "Marketing analytics team",
    identifier: "marketing-analytics@acme.com",
    type: "team",
    platform: "google_groups",
    purposes: ["Campaign targeting", "Audience segmentation"],
    datasets: [
      "hubspot_contacts",
      "mailchimp_lists",
      "bigquery_events",
      "segment_events",
    ],
    findingsCount: 3,
    linkedSystem: null,
  },
  {
    id: "2",
    name: "CS support agent",
    identifier: "agent:cs-support-v2",
    type: "ai_agent",
    platform: "service_account",
    purposes: ["Customer support", "Ticket resolution"],
    datasets: ["zendesk_tickets", "intercom_conversations"],
    findingsCount: 2,
    // 2 policy deviations
    linkedSystem: null,
  },
  {
    id: "3",
    name: "Data science — churn model",
    identifier: "ds-churn-project@acme.com",
    type: "project",
    platform: "okta",
    purposes: ["Predictive analytics"],
    datasets: ["bigquery_users", "databricks_ml", "snowflake_analytics"],
    findingsCount: 0,
    linkedSystem: null,
  },
  {
    id: "4",
    name: "Fraud detection agent",
    identifier: "agent:fraud-detect-prod",
    type: "ai_agent",
    platform: "service_account",
    purposes: ["Fraud prevention", "Transaction monitoring"],
    datasets: [
      "stripe_transactions",
      "stripe_customers",
      "sift_events",
      "postgres_fraud_logs",
    ],
    findingsCount: 0,
    linkedSystem: null,
  },
  {
    id: "5",
    name: "Customer data platform",
    identifier: "Linked to system: CDP Production",
    type: "system",
    platform: null,
    purposes: ["Profile unification", "Campaign targeting", "Analytics"],
    datasets: ["segment_events", "bigquery_users"],
    findingsCount: 1,
    linkedSystem: "cdp-production",
  },
  {
    id: "6",
    name: "Engineering — backend",
    identifier: "eng-backend@acme.com",
    type: "team",
    platform: "google_groups",
    purposes: [],
    datasets: [],
    findingsCount: 0,
    linkedSystem: null,
  },
  {
    id: "7",
    name: "HR operations",
    identifier: "hr-ops@acme.com",
    type: "team",
    platform: "active_directory",
    purposes: ["Employee admin", "Payroll processing"],
    datasets: ["workday_employees", "adp_payroll"],
    findingsCount: 0,
    linkedSystem: null,
  },
  {
    id: "8",
    name: "Product analytics",
    identifier: "product-analytics@acme.com",
    type: "team",
    platform: "google_groups",
    purposes: ["Product improvement", "Usage analytics"],
    datasets: ["bigquery_product", "amplitude_product", "segment_events"],
    findingsCount: 0,
    linkedSystem: null,
  },
  {
    id: "9",
    name: "Compliance reporting",
    identifier: "compliance-reporting@acme.com",
    type: "project",
    platform: "okta",
    purposes: ["Regulatory reporting"],
    datasets: ["adp_payroll", "workday_employees"],
    findingsCount: 0,
    linkedSystem: null,
  },
  {
    id: "10",
    name: "Email service",
    identifier: "Linked to system: SendGrid",
    type: "system",
    platform: null,
    purposes: ["Transactional email", "Marketing email"],
    datasets: ["mailchimp_lists", "hubspot_contacts"],
    findingsCount: 0,
    linkedSystem: "sendgrid",
  },
  {
    id: "11",
    name: "Data pipeline service account",
    identifier: "svc:etl-pipeline-prod",
    type: "service_account",
    platform: "service_account",
    purposes: [],
    datasets: [],
    findingsCount: 0,
    linkedSystem: null,
  },
  {
    id: "12",
    name: "Recommendation engine",
    identifier: "agent:reco-engine-v3",
    type: "ai_agent",
    platform: "service_account",
    purposes: ["Personalization", "Product improvement"],
    datasets: ["databricks_ml", "amplitude_events", "segment_profiles"],
    findingsCount: 0,
    linkedSystem: null,
  },
];

export const UNRESOLVED_ACCESSOR_COUNT = 3;

export const MOCK_VIOLATIONS: ConsumerViolation[] = [
  {
    id: "v1",
    consumerId: "1",
    dataset: "Snowflake — raw_events",
    table: "user_sessions",
    accessedAt: "2026-03-30T09:14:00Z",
    description:
      "Accessed user_sessions which contains behavioral data not covered by declared purposes (Campaign targeting, Audience segmentation).",
  },
  {
    id: "v2",
    consumerId: "1",
    dataset: "Snowflake — raw_events",
    table: "payment_transactions",
    accessedAt: "2026-03-29T15:42:00Z",
    description:
      "Accessed payment_transactions containing financial data outside declared purpose scope.",
  },
  {
    id: "v3",
    consumerId: "1",
    dataset: "BigQuery — customer_pii",
    table: "identity_documents",
    accessedAt: "2026-03-28T11:03:00Z",
    description:
      "Accessed identity_documents containing government ID data with no matching purpose.",
  },
  {
    id: "v4",
    consumerId: "1",
    dataset: "PostgreSQL — app_db",
    table: "user_preferences",
    accessedAt: "2026-03-27T08:51:00Z",
    description:
      "Accessed user_preferences which is not assigned to any of this consumer's declared purposes.",
  },
  {
    id: "v5",
    consumerId: "2",
    dataset: "PostgreSQL — app_db",
    table: "employee_records",
    accessedAt: "2026-03-30T13:22:00Z",
    description:
      "Accessed employee_records containing HR data outside declared purposes (Customer support, Ticket resolution).",
  },
  {
    id: "v6",
    consumerId: "2",
    dataset: "Snowflake — analytics",
    table: "revenue_metrics",
    accessedAt: "2026-03-29T10:05:00Z",
    description:
      "Accessed revenue_metrics containing financial analytics not covered by support purposes.",
  },
  {
    id: "v7",
    consumerId: "5",
    dataset: "Segment — events",
    table: "raw_clickstream",
    accessedAt: "2026-03-30T16:38:00Z",
    description:
      "Accessed raw_clickstream behavioral data not covered by declared purposes (Profile unification, Campaign targeting, Analytics).",
  },
];

export const MOCK_VIOLATION_GROUPS: Record<string, PolicyViolationGroup[]> = {
  "1": [
    {
      purpose: "Campaign targeting",
      totalQueries: 847,
      datasets: [
        {
          name: "Snowflake — raw_events",
          tables: ["payment_transactions", "user_sessions"],
          queryCount: 612,
          lastSeen: "2026-03-30T09:14:00Z",
        },
        {
          name: "BigQuery — customer_pii",
          tables: ["identity_documents"],
          queryCount: 235,
          lastSeen: "2026-03-28T11:03:00Z",
        },
      ],
    },
    {
      purpose: "Audience segmentation",
      totalQueries: 203,
      datasets: [
        {
          name: "PostgreSQL — app_db",
          tables: ["user_preferences", "account_settings"],
          queryCount: 203,
          lastSeen: "2026-03-27T08:51:00Z",
        },
      ],
    },
  ],
  "2": [
    {
      purpose: "Customer support",
      totalQueries: 156,
      datasets: [
        {
          name: "PostgreSQL — app_db",
          tables: ["employee_records"],
          queryCount: 98,
          lastSeen: "2026-03-30T13:22:00Z",
        },
      ],
    },
    {
      purpose: "Ticket resolution",
      totalQueries: 72,
      datasets: [
        {
          name: "Snowflake — analytics",
          tables: ["revenue_metrics"],
          queryCount: 72,
          lastSeen: "2026-03-29T10:05:00Z",
        },
      ],
    },
  ],
  "5": [
    {
      purpose: "Profile unification",
      totalQueries: 41,
      datasets: [
        {
          name: "Segment — events",
          tables: ["raw_clickstream"],
          queryCount: 41,
          lastSeen: "2026-03-30T16:38:00Z",
        },
      ],
    },
  ],
};

export const MOCK_POLICY_GAPS: Record<string, PolicyGap[]> = {
  "1": [
    {
      dataset: "Snowflake — ml_features",
      tables: ["churn_predictions", "ltv_scores"],
      queryCount: 312,
      lastSeen: "2026-03-30T14:22:00Z",
      description:
        "This consumer is querying ML feature tables that don't fall under any declared purpose. Consider creating a purpose like \"Predictive analytics\" to cover this activity.",
    },
  ],
};
