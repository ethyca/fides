import type { DataPurposeResponse } from "~/types/api";

// Local UI-only types for data that has no backend endpoint yet.
// These will move to the slice in step 2 and eventually to ~/types/api
// once the backend endpoints land.

export interface PurposeSystemAssignment {
  system_id: string;
  system_name: string;
  system_type: string;
  assigned: boolean;
  consumer_category?: "system" | "group";
}

export interface PurposeDatasetAssignment {
  dataset_fides_key: string;
  dataset_name: string;
  system_name: string;
  collection_count: number;
  data_categories: string[];
  updated_at: string;
  steward: string;
}

export interface AvailableSystem {
  system_id: string;
  system_name: string;
  system_type: string;
}

export interface AvailableDataset {
  dataset_fides_key: string;
  dataset_name: string;
  system_name: string;
}

export const mockDataPurposes: DataPurposeResponse[] = [
  {
    id: "customer_analytics",
    fides_key: "customer_analytics",
    name: "Customer Analytics",
    description:
      "Collect and analyze customer behavior data to understand engagement patterns, conversion funnels, and product usage across platforms.",
    data_use: "analytics",
    data_categories: ["user.behavior", "system.operations"],
    data_subject: "customer",
    legal_basis_for_processing: "Legitimate interests",
    flexible_legal_basis_for_processing: false,
    special_category_legal_basis: null,
    retention_period: "365",
    features: ["profiling"],
    created_at: "2026-01-10T09:00:00Z",
    updated_at: "2026-03-24T14:30:00Z",
  },
  {
    id: "email_campaign_targeting",
    fides_key: "email_campaign_targeting",
    name: "Email Campaign Targeting",
    description:
      "Use customer contact and preference data to send targeted marketing emails, newsletters, and promotional offers.",
    data_use: "marketing.advertising",
    data_categories: ["user.contact.email", "user.behavior"],
    data_subject: "customer",
    legal_basis_for_processing: "Consent",
    flexible_legal_basis_for_processing: true,
    special_category_legal_basis: null,
    retention_period: "180",
    features: ["linking_devices"],
    created_at: "2026-01-15T09:00:00Z",
    updated_at: "2026-03-18T16:45:00Z",
  },
  {
    id: "fraud_detection",
    fides_key: "fraud_detection",
    name: "Fraud Detection & Prevention",
    description:
      "Process transaction, device, and behavioral data to detect, prevent, and investigate fraudulent activities in real time.",
    data_use: "essential.service.security",
    data_categories: [
      "user.financial",
      "user.behavior",
      "system.operations",
      "user.device",
    ],
    data_subject: "customer",
    legal_basis_for_processing: "Legitimate interests",
    flexible_legal_basis_for_processing: false,
    special_category_legal_basis: null,
    retention_period: "730",
    features: ["automated_decisions", "profiling"],
    created_at: "2026-01-20T09:00:00Z",
    updated_at: "2026-03-25T13:00:00Z",
  },
  {
    id: "customer_support_ops",
    fides_key: "customer_support_ops",
    name: "Customer Support Operations",
    description:
      "Collect and process customer data to provide support services, resolve issues, and manage support ticket workflows.",
    data_use: "essential.service.operations",
    data_categories: ["user.contact", "user.account"],
    data_subject: "customer",
    legal_basis_for_processing: "Contract",
    flexible_legal_basis_for_processing: false,
    special_category_legal_basis: null,
    retention_period: "365",
    features: [],
    created_at: "2026-01-22T09:00:00Z",
    updated_at: "2026-03-23T17:10:00Z",
  },
  {
    id: "hr_employee_management",
    fides_key: "hr_employee_management",
    name: "HR Employee Management",
    description:
      "Process employee personal data for payroll, benefits administration, performance management, and regulatory compliance.",
    data_use: "essential.service.operations",
    data_categories: ["user.contact", "user.financial", "user.government_id"],
    data_subject: "employee",
    legal_basis_for_processing: "Contract",
    flexible_legal_basis_for_processing: false,
    special_category_legal_basis: "employment",
    retention_period: "2555",
    features: [],
    created_at: "2026-01-25T09:00:00Z",
    updated_at: "2026-03-19T14:00:00Z",
  },
  {
    id: "feature_adoption",
    fides_key: "feature_adoption",
    name: "Feature Adoption Tracking",
    description:
      "Track how users discover and adopt new product features to inform roadmap prioritization and onboarding improvements.",
    data_use: "improve",
    data_categories: ["user.behavior", "system.operations"],
    data_subject: "customer",
    legal_basis_for_processing: "Legitimate interests",
    flexible_legal_basis_for_processing: true,
    special_category_legal_basis: null,
    retention_period: "365",
    features: ["profiling"],
    created_at: "2026-02-01T09:00:00Z",
    updated_at: "2026-03-24T09:45:00Z",
  },
];

export const mockPurposeSystems: Record<string, PurposeSystemAssignment[]> = {
  customer_analytics: [
    {
      system_id: "bigquery",
      system_name: "BigQuery",
      system_type: "Data warehouse",
      assigned: true,
      consumer_category: "system",
    },
    {
      system_id: "snowflake",
      system_name: "Snowflake",
      system_type: "Data warehouse",
      assigned: true,
      consumer_category: "system",
    },
    {
      system_id: "amplitude",
      system_name: "Amplitude",
      system_type: "Analytics",
      assigned: true,
      consumer_category: "system",
    },
    {
      system_id: "segment",
      system_name: "Segment",
      system_type: "CDP",
      assigned: true,
      consumer_category: "system",
    },
    {
      system_id: "mixpanel",
      system_name: "Mixpanel",
      system_type: "Analytics",
      assigned: true,
      consumer_category: "system",
    },
    {
      system_id: "marketing_analytics_group",
      system_name: "Marketing analytics team",
      system_type: "Google group",
      assigned: true,
      consumer_category: "group",
    },
    {
      system_id: "data_science_group",
      system_name: "Data science team",
      system_type: "Google group",
      assigned: true,
      consumer_category: "group",
    },
    {
      system_id: "looker",
      system_name: "Looker",
      system_type: "BI",
      assigned: true,
      consumer_category: "system",
    },
    {
      system_id: "databricks",
      system_name: "Databricks",
      system_type: "Data platform",
      assigned: true,
      consumer_category: "system",
    },
    {
      system_id: "fullstory",
      system_name: "FullStory",
      system_type: "Session replay",
      assigned: true,
      consumer_category: "system",
    },
  ],
  email_campaign_targeting: [
    {
      system_id: "hubspot",
      system_name: "HubSpot",
      system_type: "CRM",
      assigned: true,
    },
    {
      system_id: "mailchimp",
      system_name: "Mailchimp",
      system_type: "Email marketing",
      assigned: true,
    },
    {
      system_id: "google_ads",
      system_name: "Google Ads",
      system_type: "Advertising",
      assigned: false,
    },
  ],
  fraud_detection: [
    {
      system_id: "stripe",
      system_name: "Stripe",
      system_type: "Payment processor",
      assigned: true,
    },
    {
      system_id: "sift",
      system_name: "Sift",
      system_type: "Fraud detection",
      assigned: true,
    },
    {
      system_id: "postgres_prod",
      system_name: "PostgreSQL (prod)",
      system_type: "Database",
      assigned: true,
    },
  ],
  hr_employee_management: [
    {
      system_id: "workday",
      system_name: "Workday",
      system_type: "HRIS",
      assigned: true,
    },
    {
      system_id: "adp",
      system_name: "ADP",
      system_type: "Payroll",
      assigned: true,
    },
  ],
  feature_adoption: [
    {
      system_id: "bigquery",
      system_name: "BigQuery",
      system_type: "Data warehouse",
      assigned: true,
    },
    {
      system_id: "amplitude",
      system_name: "Amplitude",
      system_type: "Analytics",
      assigned: true,
    },
    {
      system_id: "sentry",
      system_name: "Sentry",
      system_type: "Error tracking",
      assigned: true,
    },
    {
      system_id: "segment",
      system_name: "Segment",
      system_type: "CDP",
      assigned: true,
    },
  ],
  customer_support_ops: [
    {
      system_id: "zendesk",
      system_name: "Zendesk",
      system_type: "Support platform",
      assigned: true,
    },
    {
      system_id: "intercom",
      system_name: "Intercom",
      system_type: "Messaging",
      assigned: true,
    },
    {
      system_id: "salesforce",
      system_name: "Salesforce",
      system_type: "CRM",
      assigned: false,
    },
  ],
};

export const mockPurposeDatasets: Record<string, PurposeDatasetAssignment[]> = {
  customer_analytics: [
    {
      dataset_fides_key: "bigquery_sessions",
      dataset_name: "BigQuery Sessions",
      system_name: "BigQuery",
      collection_count: 3,
      data_categories: ["user.behavior", "system.operations"],
      updated_at: "2026-03-28T09:05:00Z",
      steward: "Marcus Taylor",
    },
    {
      dataset_fides_key: "bigquery_events",
      dataset_name: "BigQuery Events",
      system_name: "BigQuery",
      collection_count: 12,
      data_categories: ["user.behavior", "system.operations"],
      updated_at: "2026-04-02T10:14:00Z",
      steward: "Sarah Chen",
    },
    {
      dataset_fides_key: "bigquery_users",
      dataset_name: "BigQuery Users",
      system_name: "BigQuery",
      collection_count: 5,
      data_categories: ["user.behavior", "user.contact.email"],
      updated_at: "2026-04-05T16:30:00Z",
      steward: "Sarah Chen",
    },
    {
      dataset_fides_key: "bigquery_pageviews",
      dataset_name: "BigQuery Pageviews",
      system_name: "BigQuery",
      collection_count: 2,
      data_categories: ["user.behavior", "user.device"],
      updated_at: "2026-04-10T12:40:00Z",
      steward: "Marcus Taylor",
    },
    {
      dataset_fides_key: "snowflake_analytics",
      dataset_name: "Snowflake Analytics",
      system_name: "Snowflake",
      collection_count: 15,
      data_categories: ["user.behavior", "system.operations"],
      updated_at: "2026-04-01T08:22:00Z",
      steward: "Priya Desai",
    },
  ],
  email_campaign_targeting: [
    {
      dataset_fides_key: "hubspot_contacts",
      dataset_name: "HubSpot Contacts",
      system_name: "HubSpot",
      collection_count: 6,
      data_categories: ["user.contact.email", "user.behavior"],
      updated_at: "2026-03-30T09:00:00Z",
      steward: "Jordan Lee",
    },
    {
      dataset_fides_key: "mailchimp_lists",
      dataset_name: "Mailchimp Lists",
      system_name: "Mailchimp",
      collection_count: 3,
      data_categories: ["user.contact.email"],
      updated_at: "2026-03-25T14:00:00Z",
      steward: "Emma Rivera",
    },
    {
      dataset_fides_key: "mailchimp_campaigns",
      dataset_name: "Mailchimp Campaigns",
      system_name: "Mailchimp",
      collection_count: 5,
      data_categories: ["user.contact.email", "user.behavior"],
      updated_at: "2026-03-29T17:00:00Z",
      steward: "Emma Rivera",
    },
    {
      dataset_fides_key: "google_ads_campaigns",
      dataset_name: "Google Ads Campaigns",
      system_name: "Google Ads",
      collection_count: 7,
      data_categories: ["user.behavior"],
      updated_at: "2026-03-27T10:45:00Z",
      steward: "Alex Park",
    },
    {
      dataset_fides_key: "salesforce_leads",
      dataset_name: "Salesforce Leads",
      system_name: "Salesforce",
      collection_count: 8,
      data_categories: ["user.contact.email", "user.behavior"],
      updated_at: "2026-04-01T13:20:00Z",
      steward: "Jordan Lee",
    },
  ],
  fraud_detection: [
    {
      dataset_fides_key: "stripe_transactions",
      dataset_name: "Stripe Transactions",
      system_name: "Stripe",
      collection_count: 9,
      data_categories: ["user.financial", "user.device"],
      updated_at: "2026-03-30T10:00:00Z",
      steward: "Dana Ahmed",
    },
    {
      dataset_fides_key: "stripe_customers",
      dataset_name: "Stripe Customers",
      system_name: "Stripe",
      collection_count: 5,
      data_categories: ["user.financial", "user.behavior"],
      updated_at: "2026-03-29T11:00:00Z",
      steward: "Dana Ahmed",
    },
    {
      dataset_fides_key: "sift_events",
      dataset_name: "Sift Events",
      system_name: "Sift",
      collection_count: 4,
      data_categories: ["user.behavior", "user.device"],
      updated_at: "2026-04-01T09:00:00Z",
      steward: "Noah Kim",
    },
    {
      dataset_fides_key: "postgres_fraud_logs",
      dataset_name: "Fraud Logs",
      system_name: "PostgreSQL (prod)",
      collection_count: 7,
      data_categories: ["system.operations", "user.behavior", "user.device"],
      updated_at: "2026-04-03T12:00:00Z",
      steward: "Riya Gupta",
    },
    {
      dataset_fides_key: "postgres_users",
      dataset_name: "Users DB",
      system_name: "PostgreSQL (prod)",
      collection_count: 12,
      data_categories: ["user.financial", "user.behavior"],
      updated_at: "2026-04-04T10:30:00Z",
      steward: "Riya Gupta",
    },
  ],
  hr_employee_management: [
    {
      dataset_fides_key: "workday_employees",
      dataset_name: "Workday Employees",
      system_name: "Workday",
      collection_count: 10,
      data_categories: ["user.contact", "user.government_id"],
      updated_at: "2026-03-25T09:00:00Z",
      steward: "Lena Brooks",
    },
    {
      dataset_fides_key: "workday_benefits",
      dataset_name: "Workday Benefits",
      system_name: "Workday",
      collection_count: 6,
      data_categories: ["user.contact", "user.financial"],
      updated_at: "2026-03-26T10:00:00Z",
      steward: "Lena Brooks",
    },
    {
      dataset_fides_key: "adp_payroll",
      dataset_name: "ADP Payroll",
      system_name: "ADP",
      collection_count: 8,
      data_categories: ["user.contact", "user.financial", "user.government_id"],
      updated_at: "2026-03-28T12:00:00Z",
      steward: "Miguel Hart",
    },
  ],
  feature_adoption: [
    {
      dataset_fides_key: "bigquery_product",
      dataset_name: "BigQuery Product Data",
      system_name: "BigQuery",
      collection_count: 14,
      data_categories: ["user.behavior", "system.operations"],
      updated_at: "2026-04-01T09:00:00Z",
      steward: "Sarah Chen",
    },
    {
      dataset_fides_key: "amplitude_product",
      dataset_name: "Amplitude Product",
      system_name: "Amplitude",
      collection_count: 6,
      data_categories: ["user.behavior", "user.device"],
      updated_at: "2026-04-02T10:00:00Z",
      steward: "Marcus Taylor",
    },
    {
      dataset_fides_key: "sentry_errors",
      dataset_name: "Sentry Errors",
      system_name: "Sentry",
      collection_count: 3,
      data_categories: ["system.operations", "user.device"],
      updated_at: "2026-04-04T12:00:00Z",
      steward: "Ben Morales",
    },
    {
      dataset_fides_key: "segment_events",
      dataset_name: "Segment Events",
      system_name: "Segment",
      collection_count: 11,
      data_categories: ["user.behavior"],
      updated_at: "2026-04-06T14:00:00Z",
      steward: "Priya Desai",
    },
  ],
  customer_support_ops: [
    {
      dataset_fides_key: "zendesk_tickets",
      dataset_name: "Zendesk Tickets",
      system_name: "Zendesk",
      collection_count: 5,
      data_categories: [],
      updated_at: "2026-03-20T09:00:00Z",
      steward: "Ava Sullivan",
    },
    {
      dataset_fides_key: "intercom_conversations",
      dataset_name: "Intercom Conversations",
      system_name: "Intercom",
      collection_count: 4,
      data_categories: [],
      updated_at: "2026-03-23T12:00:00Z",
      steward: "Owen Fischer",
    },
    {
      dataset_fides_key: "salesforce_cases",
      dataset_name: "Salesforce Cases",
      system_name: "Salesforce",
      collection_count: 7,
      data_categories: [],
      updated_at: "2026-03-25T14:00:00Z",
      steward: "Jordan Lee",
    },
  ],
};

export const mockAvailableSystems: AvailableSystem[] = [
  {
    system_id: "bigquery",
    system_name: "BigQuery",
    system_type: "Data warehouse",
  },
  {
    system_id: "snowflake",
    system_name: "Snowflake",
    system_type: "Data warehouse",
  },
  {
    system_id: "amplitude",
    system_name: "Amplitude",
    system_type: "Analytics",
  },
  { system_id: "mixpanel", system_name: "Mixpanel", system_type: "Analytics" },
  { system_id: "segment", system_name: "Segment", system_type: "CDP" },
  { system_id: "looker", system_name: "Looker", system_type: "BI" },
  { system_id: "hubspot", system_name: "HubSpot", system_type: "CRM" },
  { system_id: "salesforce", system_name: "Salesforce", system_type: "CRM" },
  {
    system_id: "mailchimp",
    system_name: "Mailchimp",
    system_type: "Email marketing",
  },
  {
    system_id: "google_ads",
    system_name: "Google Ads",
    system_type: "Advertising",
  },
  {
    system_id: "stripe",
    system_name: "Stripe",
    system_type: "Payment processor",
  },
  { system_id: "sift", system_name: "Sift", system_type: "Fraud detection" },
  { system_id: "workday", system_name: "Workday", system_type: "HRIS" },
  { system_id: "adp", system_name: "ADP", system_type: "Payroll" },
  { system_id: "sentry", system_name: "Sentry", system_type: "Error tracking" },
  {
    system_id: "zendesk",
    system_name: "Zendesk",
    system_type: "Support platform",
  },
  { system_id: "intercom", system_name: "Intercom", system_type: "Messaging" },
];

export const mockAvailableDatasets: AvailableDataset[] = [
  {
    dataset_fides_key: "bigquery_events",
    dataset_name: "BigQuery Events",
    system_name: "BigQuery",
  },
  {
    dataset_fides_key: "bigquery_users",
    dataset_name: "BigQuery Users",
    system_name: "BigQuery",
  },
  {
    dataset_fides_key: "snowflake_analytics",
    dataset_name: "Snowflake Analytics",
    system_name: "Snowflake",
  },
  {
    dataset_fides_key: "amplitude_events",
    dataset_name: "Amplitude Events",
    system_name: "Amplitude",
  },
  {
    dataset_fides_key: "hubspot_contacts",
    dataset_name: "HubSpot Contacts",
    system_name: "HubSpot",
  },
  {
    dataset_fides_key: "mailchimp_lists",
    dataset_name: "Mailchimp Lists",
    system_name: "Mailchimp",
  },
  {
    dataset_fides_key: "stripe_transactions",
    dataset_name: "Stripe Transactions",
    system_name: "Stripe",
  },
  {
    dataset_fides_key: "sift_events",
    dataset_name: "Sift Events",
    system_name: "Sift",
  },
  {
    dataset_fides_key: "workday_employees",
    dataset_name: "Workday Employees",
    system_name: "Workday",
  },
  {
    dataset_fides_key: "adp_payroll",
    dataset_name: "ADP Payroll",
    system_name: "ADP",
  },
  {
    dataset_fides_key: "sentry_errors",
    dataset_name: "Sentry Errors",
    system_name: "Sentry",
  },
  {
    dataset_fides_key: "zendesk_tickets",
    dataset_name: "Zendesk Tickets",
    system_name: "Zendesk",
  },
  {
    dataset_fides_key: "salesforce_accounts",
    dataset_name: "Salesforce Accounts",
    system_name: "Salesforce",
  },
];
