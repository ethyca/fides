import type {
  ActivityFeedItem,
  AgentBriefingResponse,
  PostureResponse,
  PriorityAction,
  PrivacyRequestsResponse,
  SystemCoverageResponse,
  TrendsResponse,
} from "~/features/dashboard/types";
import {
  ActionSeverity,
  ActionStatus,
  ActionType,
  DiffDirection,
  PostureBand,
} from "~/features/dashboard/types";

export const mockPosture: PostureResponse = {
  score: 64,
  band: PostureBand.GOOD,
  diff_percent: 3.8,
  diff_direction: DiffDirection.UP,
  agent_annotation:
    "Up 3.8 points this week, driven by Casey completing 34 classification reviews across Snowflake and BigQuery.",
  dimensions: [
    {
      dimension: "coverage",
      label: "Coverage",
      weight: 0.3,
      score: 71,
      band: PostureBand.GOOD,
    },
    {
      dimension: "classification_health",
      label: "Classification Health",
      weight: 0.23,
      score: 58,
      band: PostureBand.AT_RISK,
    },
    {
      dimension: "dsr_compliance",
      label: "DSR Compliance",
      weight: 0.23,
      score: 74,
      band: PostureBand.GOOD,
    },
    {
      dimension: "consent_alignment",
      label: "Consent Alignment",
      weight: 0.24,
      score: 28,
      band: PostureBand.CRITICAL,
    },
  ],
};

export const mockSystemCoverage: SystemCoverageResponse = {
  total_systems: 47,
  fully_classified: 34,
  partially_classified: 7,
  unclassified: 6,
  without_steward: 4,
  coverage_percentage: 72,
};

export const mockPriorityActions: PriorityAction[] = [
  {
    id: "act-001",
    type: ActionType.DSR_ACTION,
    severity: ActionSeverity.CRITICAL,

    title: "Overdue erasure request",
    message: "DSR-4521 is 34 days overdue. SLA breach since Feb 9, 2026.",
    agent_summary:
      "This erasure request for a California resident exceeded the 45-day CCPA deadline on February 9th. The request is blocked on a manual verification step in Salesforce. Continued delay increases regulatory exposure.",
    due_date: "2026-02-09",
    action_data: {
      request_id: "pri-4521",
      regulation: "ccpa",
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-002",
    type: ActionType.POLICY_VIOLATION,
    severity: ActionSeverity.CRITICAL,

    title: "CCPA retention policy violation",
    message:
      "HubSpot CRM retaining contact data beyond 24-month policy limit. 12,400 records affected.",
    agent_summary:
      "Fides detected that HubSpot CRM contains 12,400 contact records older than your 24-month CCPA retention policy. This was flagged during the latest enforcement scan. The system's data retention configuration needs to be updated.",
    due_date: "2026-03-18",
    action_data: {
      system_id: "sys-hubspot",
      violation_type: "retention",
      records_affected: 12400,
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-003",
    type: ActionType.CONSENT_ANOMALY,
    severity: ActionSeverity.HIGH,

    title: "Consent opt-in rate drop",
    message:
      "Marketing consent opt-in rate dropped from 78% to 34% on mobile web in the last 48 hours.",
    agent_summary:
      "A significant drop in marketing consent opt-in rates was detected on the mobile web property. This could indicate a consent banner rendering issue, a UX change that made opt-in harder, or a genuine shift in user preference. Investigate the consent reporting dashboard for the mobile web channel.",
    due_date: "2026-03-17",
    action_data: {
      channel: "mobile_web",
      previous_rate: 0.78,
      current_rate: 0.34,
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-004",
    type: ActionType.CLASSIFICATION_REVIEW,
    severity: ActionSeverity.MEDIUM,

    title: "12 new classifications pending review",
    message:
      "Helios detected 12 new data classifications across Snowflake, BigQuery, and Redshift. 8 are high-confidence (>95%).",
    agent_summary:
      "The latest Helios scan identified 12 new field classifications across 3 systems. 8 have confidence scores above 95% and could be auto-approved. The remaining 4 include potentially sensitive categories (biometric, health) that warrant manual review.",
    due_date: "2026-03-20",
    action_data: {
      total_classifications: 12,
      high_confidence_count: 8,
      systems: ["snowflake-prod", "bigquery-analytics", "redshift-warehouse"],
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-005",
    type: ActionType.STEWARD_ASSIGNMENT,
    severity: ActionSeverity.MEDIUM,

    title: "3 HR systems need data stewards",
    message:
      "Workday, BambooHR, and ADP have no assigned data steward. These systems process employee PII.",
    agent_summary:
      "Three HR systems containing sensitive employee data (SSNs, compensation, health plan selections) have no assigned data steward. Without stewards, classification reviews, DSR fulfillment, and PIA assessments cannot be routed to the right person.",
    due_date: "2026-03-22",
    action_data: {
      system_ids: ["sys-workday", "sys-bamboohr", "sys-adp"],
      system_names: ["Workday", "BambooHR", "ADP"],
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-006",
    type: ActionType.DSR_ACTION,
    severity: ActionSeverity.MEDIUM,

    title: "DSR approaching SLA deadline",
    message:
      "Access request DSR-4587 has 5 days remaining. Pending manual step in Stripe.",
    agent_summary:
      "This access request is on track but requires a manual data export from Stripe. The assigned steward (Jamie Torres) has not yet completed the step. 5 days remain before SLA breach.",
    due_date: "2026-03-20",
    action_data: {
      request_id: "pri-4587",
      regulation: "gdpr",
      pending_system: "Stripe",
    },
    status: ActionStatus.IN_PROGRESS,
  },
  {
    id: "act-007",
    type: ActionType.SYSTEM_REVIEW,
    severity: ActionSeverity.LOW,

    title: "New system detected: Amplitude",
    message:
      "Helios discovered an unregistered system 'Amplitude' receiving user event data from your web application.",
    agent_summary:
      "During network traffic analysis, Helios identified data flowing to Amplitude (analytics platform) that is not registered in your system inventory. This system likely processes behavioral and device data. Review and register it to ensure governance coverage.",
    due_date: null,
    action_data: {
      system_name: "Amplitude",
      detected_data_categories: ["user.behavior", "user.device"],
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-008",
    type: ActionType.PIA_UPDATE,
    severity: ActionSeverity.LOW,

    title: "Privacy impact assessment needs update",
    message:
      "PIA for the Segment CDP integration was last completed 11 months ago. Annual review recommended.",
    agent_summary:
      "Your organization's policy recommends annual PIA reviews. The Segment CDP integration PIA was completed in April 2025. While not overdue by regulation, refreshing the assessment ensures it reflects any changes to data flows or processing purposes.",
    due_date: null,
    action_data: {
      system_id: "sys-segment",
      last_assessment_date: "2025-04-12",
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-009",
    type: ActionType.DSR_ACTION,
    severity: ActionSeverity.CRITICAL,

    title: "Overdue access request from EU resident",
    message:
      "DSR-4602 exceeded the 30-day GDPR deadline on Mar 2. Blocked on identity verification in Zendesk.",
    agent_summary:
      "A GDPR access request has been pending for 44 days. The identity verification step in Zendesk has not been completed by the assigned steward.",
    due_date: "2026-03-02",
    action_data: {
      request_id: "pri-4602",
      regulation: "gdpr",
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-010",
    type: ActionType.CONSENT_ANOMALY,
    severity: ActionSeverity.CRITICAL,

    title: "Analytics tracking without consent",
    message:
      "Google Analytics firing on EU pages before consent is granted. Detected on 3 properties.",
    agent_summary:
      "Fides detected Google Analytics tags executing prior to consent collection on three EU-targeted web properties. This represents a potential ePrivacy and GDPR violation.",
    due_date: "2026-03-17",
    action_data: {
      properties: ["eu-main", "eu-shop", "eu-blog"],
      vendor: "Google Analytics",
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-011",
    type: ActionType.CLASSIFICATION_REVIEW,
    severity: ActionSeverity.HIGH,

    title: "Sensitive health data detected in Postgres",
    message:
      "Helios classified 4 fields in the users table as health-related. Confidence: 87–92%.",
    agent_summary:
      "Fields in the main Postgres users table were classified as health data. These are below the auto-approve threshold and require manual confirmation before enforcement rules apply.",
    due_date: "2026-03-19",
    action_data: {
      total_classifications: 4,
      high_confidence_count: 0,
      systems: ["postgres-prod"],
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-012",
    type: ActionType.POLICY_VIOLATION,
    severity: ActionSeverity.HIGH,

    title: "Salesforce storing SSNs without encryption",
    message:
      "5,200 records in Salesforce contain unencrypted SSN fields. Policy requires encryption at rest.",
    agent_summary:
      "A policy scan found unencrypted Social Security Numbers in a custom Salesforce object. Your data handling policy requires encryption at rest for all government identifiers.",
    due_date: "2026-03-18",
    action_data: {
      system_id: "sys-salesforce",
      violation_type: "encryption",
      records_affected: 5200,
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-013",
    type: ActionType.STEWARD_ASSIGNMENT,
    severity: ActionSeverity.MEDIUM,

    title: "Marketing systems missing steward",
    message: "Marketo, Mailchimp, and Iterable have no assigned data steward.",
    agent_summary:
      "Three marketing automation systems processing contact and behavioral data have no steward. Assignment is needed to route classification and consent reviews.",
    due_date: "2026-03-25",
    action_data: {
      system_ids: ["sys-marketo", "sys-mailchimp", "sys-iterable"],
      system_names: ["Marketo", "Mailchimp", "Iterable"],
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-014",
    type: ActionType.DSR_ACTION,
    severity: ActionSeverity.MEDIUM,

    title: "Bulk erasure batch stalled",
    message:
      "Batch erasure job for 48 records paused after Snowflake connector timeout.",
    agent_summary:
      "A bulk erasure operation covering 48 data subject records stopped after the Snowflake connector timed out. 31 of 48 records were processed. The remaining 17 need manual retry.",
    due_date: "2026-03-21",
    action_data: {
      request_id: "pri-batch-12",
      pending_system: "Snowflake",
    },
    status: ActionStatus.IN_PROGRESS,
  },
  {
    id: "act-015",
    type: ActionType.SYSTEM_REVIEW,
    severity: ActionSeverity.LOW,

    title: "New system detected: Mixpanel",
    message:
      "Helios found data flowing to Mixpanel from the iOS app. Not registered in your inventory.",
    agent_summary:
      "Network analysis identified Mixpanel receiving event and device data from the iOS application. This system is not in your data map.",
    due_date: null,
    action_data: {
      system_name: "Mixpanel",
      detected_data_categories: ["user.behavior", "user.device"],
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-016",
    type: ActionType.SYSTEM_REVIEW,
    severity: ActionSeverity.LOW,

    title: "New system detected: Intercom",
    message:
      "Intercom chat widget detected on support.example.com collecting user identifiers.",
    agent_summary:
      "The Intercom chat widget was found on the support subdomain, collecting email addresses and browser metadata. Register it to ensure governance coverage.",
    due_date: null,
    action_data: {
      system_name: "Intercom",
      detected_data_categories: ["user.contact.email", "user.device"],
    },
    status: ActionStatus.PENDING,
  },
  {
    id: "act-017",
    type: ActionType.PIA_UPDATE,
    severity: ActionSeverity.LOW,

    title: "Stripe PIA due for annual refresh",
    message:
      "PIA for the Stripe payment integration was last completed 13 months ago.",
    agent_summary:
      "The Stripe integration PIA was completed in February 2025. With the addition of new payment methods since then, the assessment should be refreshed.",
    due_date: null,
    action_data: {
      system_id: "sys-stripe",
      last_assessment_date: "2025-02-18",
    },
    status: ActionStatus.PENDING,
  },
];

export const mockPrivacyRequests: PrivacyRequestsResponse = {
  active_count: 47,
  statuses: { in_progress: 22, pending_action: 14, awaiting_approval: 11 },
  overdue_count: 5,
  sla_health: {
    access: { on_track: 8, approaching: 3, overdue: 1 },
    erasure: { on_track: 12, approaching: 5, overdue: 3 },
    consent: { on_track: 6, approaching: 2, overdue: 0 },
    update: { on_track: 5, approaching: 1, overdue: 1 },
  },
};

export const mockAgentBriefing: AgentBriefingResponse = {
  briefing:
    "Since you were away: Your GPS improved by 2 points after Casey approved 34 classifications across Snowflake and BigQuery. 3 DSRs completed on time. However, 1 new critical risk was detected — unclassified health data found in BigQuery project analytics-prod. Recommended action: assign a steward and initiate classification.",
  quick_actions: [
    {
      label: "Assign steward for BigQuery",
      action_type: ActionType.STEWARD_ASSIGNMENT,
      action_data: { system_id: "sys-bigquery" },
      severity: ActionSeverity.MEDIUM,
    },
    {
      label: "Review overdue DSR",
      action_type: ActionType.DSR_ACTION,
      action_data: { request_id: "pri-4521" },
      severity: ActionSeverity.CRITICAL,
    },
  ],
};

const now = Date.now();
const hoursAgo = (h: number) => new Date(now - h * 3600_000).toISOString();

export const mockActivityFeed: ActivityFeedItem[] = [
  {
    id: "af-001",
    actor_type: "agent",
    message: "Helios classified 847 fields across Snowflake and BigQuery.",
    timestamp: hoursAgo(0.5),
    event_source: "helios",
    event_type: ActionType.CLASSIFICATION_REVIEW,
    action_data: {},
  },
  {
    id: "af-002",
    actor_type: "user",
    message: "Casey approved 34 classification reviews.",
    timestamp: hoursAgo(1),
    event_source: "helios",
    event_type: ActionType.CLASSIFICATION_REVIEW,
    action_data: {},
  },
  {
    id: "af-003",
    actor_type: "system",
    message: "DSR-4521 erasure completed across 6 systems.",
    timestamp: hoursAgo(1.5),
    event_source: "lethe",
    event_type: ActionType.DSR_ACTION,
    action_data: { request_id: "pri-4521" },
  },
  {
    id: "af-004",
    actor_type: "agent",
    message: "Astralis completed privacy assessment for Stripe integration.",
    timestamp: hoursAgo(2),
    event_source: "astralis",
    event_type: ActionType.PIA_UPDATE,
    action_data: { assessment_id: "pia-stripe-01" },
  },
  {
    id: "af-005",
    actor_type: "system",
    message: "Consent preferences synced for 12,400 EU users.",
    timestamp: hoursAgo(3),
    event_source: "janus",
  },
  {
    id: "af-006",
    actor_type: "user",
    message: "Jamie Torres assigned as data steward for Workday.",
    timestamp: hoursAgo(4),
    event_type: ActionType.STEWARD_ASSIGNMENT,
    action_data: { system_id: "sys-workday" },
  },
  {
    id: "af-007",
    actor_type: "agent",
    message: "Helios detected new system: Amplitude receiving user event data.",
    timestamp: hoursAgo(5),
    event_source: "helios",
    event_type: ActionType.SYSTEM_REVIEW,
    action_data: {},
  },
  {
    id: "af-008",
    actor_type: "system",
    message: "Access request DSR-4587 auto-fulfilled via Stripe connector.",
    timestamp: hoursAgo(6),
    event_source: "lethe",
    event_type: ActionType.DSR_ACTION,
    action_data: { request_id: "pri-4587" },
  },
  {
    id: "af-009",
    actor_type: "user",
    message: "Morgan Chen updated consent notice for mobile web property.",
    timestamp: hoursAgo(8),
    event_source: "janus",
    event_type: ActionType.CONSENT_ANOMALY,
    action_data: {},
  },
  {
    id: "af-010",
    actor_type: "agent",
    message:
      "Astralis flagged policy violation: HubSpot retaining data beyond 24-month limit.",
    timestamp: hoursAgo(10),
    event_source: "astralis",
    event_type: ActionType.POLICY_VIOLATION,
    action_data: { system_id: "sys-hubspot" },
  },
  {
    id: "af-011",
    actor_type: "system",
    message: "Nightly classification scan completed — 3 new fields detected.",
    timestamp: hoursAgo(12),
    event_source: "helios",
  },
  {
    id: "af-012",
    actor_type: "user",
    message: "Alex Rivera registered BambooHR in the system inventory.",
    timestamp: hoursAgo(14),
    event_type: ActionType.SYSTEM_REVIEW,
    action_data: {},
  },
  {
    id: "af-013",
    actor_type: "agent",
    message: "Lethe processed batch erasure for 48 records across Snowflake.",
    timestamp: hoursAgo(16),
    event_source: "lethe",
    event_type: ActionType.DSR_ACTION,
    action_data: { request_id: "pri-batch-12" },
  },
  {
    id: "af-014",
    actor_type: "system",
    message: "Consent banner deployed to 3 new EU properties.",
    timestamp: hoursAgo(18),
    event_source: "janus",
  },
  {
    id: "af-015",
    actor_type: "user",
    message: "Sam Patel dismissed low-priority PIA reminder for Segment.",
    timestamp: hoursAgo(20),
    event_type: ActionType.PIA_UPDATE,
    action_data: { assessment_id: "pia-segment-01" },
  },
  {
    id: "af-016",
    actor_type: "agent",
    message: "Helios discovered Mixpanel receiving event data from iOS app.",
    timestamp: hoursAgo(24),
    event_source: "helios",
    event_type: ActionType.SYSTEM_REVIEW,
    action_data: {},
  },
  {
    id: "af-017",
    actor_type: "system",
    message:
      "Automated DSR SLA check completed — 5 requests approaching deadline.",
    timestamp: hoursAgo(28),
    event_source: "lethe",
  },
  {
    id: "af-018",
    actor_type: "user",
    message: "Taylor Kim configured Salesforce encryption policy.",
    timestamp: hoursAgo(32),
    event_type: ActionType.POLICY_VIOLATION,
    action_data: { system_id: "sys-salesforce" },
  },
  {
    id: "af-019",
    actor_type: "agent",
    message: "Janus detected consent opt-in rate drop on mobile web.",
    timestamp: hoursAgo(36),
    event_source: "janus",
    event_type: ActionType.CONSENT_ANOMALY,
    action_data: {},
  },
  {
    id: "af-020",
    actor_type: "system",
    message: "Weekly governance posture report generated. GPS: 64 (+3.8).",
    timestamp: hoursAgo(44),
  },
];

export const mockTrends: TrendsResponse = {
  metrics: {
    gps_score: {
      value: 64,
      history: [58, 59, 61, 60, 63, 62, 64],
      metadata: {},
      diff: 3.2,
    },
    dsr_volume: {
      value: 47,
      history: [8, 12, 9, 15, 11, 18, 14],
      metadata: {},
      diff: -0.08,
    },
    system_coverage: {
      value: 64.6,
      history: [55, 57, 58, 61, 60, 63, 64.6],
      metadata: {},
      diff: 2.1,
    },
    classification_health: {
      value: 58,
      history: [52, 51, 54, 55, 53, 56, 58],
      metadata: {},
      diff: 1.8,
    },
  },
};
