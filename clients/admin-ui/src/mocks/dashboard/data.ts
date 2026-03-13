import type {
  ActivityFeedItem,
  AgentBriefingResponse,
  AstralisResponse,
  PostureResponse,
  PriorityAction,
  TrendsResponse,
} from "~/features/dashboard/dashboard.slice";

export const mockPosture: PostureResponse = {
  score: 72,
  diff_percent: 4.2,
  diff_direction: "up",
  agent_annotation:
    "Your posture improved this week due to completing 3 overdue DSR requests.",
  dimensions: [
    {
      dimension: "data_mapping",
      label: "Data Mapping",
      weight: 0.25,
      score: 85,
      band: "excellent",
    },
    {
      dimension: "consent_management",
      label: "Consent Management",
      weight: 0.2,
      score: 68,
      band: "good",
    },
    {
      dimension: "dsr_fulfillment",
      label: "DSR Fulfillment",
      weight: 0.2,
      score: 74,
      band: "good",
    },
    {
      dimension: "vendor_management",
      label: "Vendor Management",
      weight: 0.15,
      score: 52,
      band: "at_risk",
    },
    {
      dimension: "risk_assessment",
      label: "Risk Assessment",
      weight: 0.2,
      score: 61,
      band: "good",
    },
  ],
};

export const mockPriorityActions: PriorityAction[] = [
  {
    id: "act-001",
    priority: 1,
    title: "Review AI-detected data classifications",
    message:
      "12 new data classifications were detected across 3 systems and need manual review.",
    agent_summary:
      "Astralis identified PII fields in the analytics database that may require updated handling policies.",
    due_date: "2026-03-15",
    action: "classification_review",
    action_data: { system_count: 3, field_count: 12 },
    status: "pending",
  },
  {
    id: "act-002",
    priority: 2,
    title: "Process overdue erasure request",
    message:
      "An erasure request from user@example.com has exceeded the 30-day SLA.",
    agent_summary:
      "This request has been pending for 34 days. The Stripe integration is blocking automated erasure.",
    due_date: "2026-03-14",
    action: "dsr_action",
    action_data: { request_id: "req-8472", days_overdue: 4 },
    status: "in_progress",
  },
  {
    id: "act-003",
    priority: 3,
    title: "New vendor system needs registration",
    message:
      "A new third-party system 'Amplitude' was detected sending user data without being registered.",
    agent_summary:
      "Network traffic analysis found outbound PII to Amplitude. This system is not in your data map.",
    due_date: "2026-03-18",
    action: "system_review",
    action_data: { system_name: "Amplitude", vendor: "Amplitude Inc." },
    status: "pending",
  },
  {
    id: "act-004",
    priority: 4,
    title: "Assign data steward for HR systems",
    message:
      "3 HR-related systems have no assigned data steward, which is required by policy.",
    agent_summary:
      "Workday, BambooHR, and Greenhouse all process employee PII but lack an assigned steward.",
    due_date: "2026-03-20",
    action: "steward_assignment",
    action_data: {
      systems: ["workday", "bamboohr", "greenhouse"],
      department: "Human Resources",
    },
    status: "pending",
  },
  {
    id: "act-005",
    priority: 5,
    title: "Consent rate anomaly on checkout page",
    message:
      "Consent opt-in rate dropped from 78% to 34% on the checkout page in the last 7 days.",
    agent_summary:
      "A recent frontend deployment may have broken the consent banner rendering on mobile devices.",
    due_date: null,
    action: "consent_anomaly",
    action_data: {
      page: "/checkout",
      previous_rate: 0.78,
      current_rate: 0.34,
    },
    status: "pending",
  },
  {
    id: "act-006",
    priority: 6,
    title: "CCPA policy violation in marketing system",
    message:
      "The marketing automation system is retaining data beyond the configured 12-month window.",
    agent_summary:
      "Scan detected 2,400 records older than 12 months in HubSpot that should have been purged.",
    due_date: null,
    action: "policy_violation",
    action_data: { system: "hubspot", records_affected: 2400, policy: "ccpa" },
    status: "pending",
  },
  {
    id: "act-007",
    priority: 7,
    title: "Privacy impact assessment needs update",
    message:
      "The PIA for the recommendation engine is over 12 months old and uses new data sources.",
    agent_summary:
      "Two new data sources (browsing history, purchase history) were added since the last assessment.",
    due_date: null,
    action: "pia_update",
    action_data: {
      system: "recommendation_engine",
      last_assessment: "2025-02-10",
    },
    status: "pending",
  },
  {
    id: "act-008",
    priority: 8,
    title: "Review newly discovered data flows",
    message:
      "5 new data flows were detected between internal systems that are not documented.",
    agent_summary:
      "Automated scanning found undocumented data transfers between the CRM and data warehouse.",
    due_date: null,
    action: "system_review",
    action_data: { flow_count: 5, source: "crm", destination: "warehouse" },
    status: "pending",
  },
];

export const mockAgentBriefing: AgentBriefingResponse = {
  briefing:
    "Good morning — Astralis resolved 4 actions overnight. 2 items need your attention: a consent anomaly in EU and an overdue erasure request.",
  quick_actions: [
    {
      id: "qa-1",
      title: "Review consent anomaly",
      action: "consent_anomaly",
      action_url: "/steward",
    },
    {
      id: "qa-2",
      title: "Process erasure request",
      action: "dsr_action",
      action_url: "/steward",
    },
  ],
};

export const mockTrends: TrendsResponse = {
  metrics: {
    data_sharing: {
      name: "Data sharing",
      value: 0.73,
      history: [0.65, 0.67, 0.68, 0.7, 0.69, 0.71, 0.72, 0.73],
      metadata: {},
      diff: 0.03,
    },
    active_users: {
      name: "Active users",
      value: 0.82,
      history: [0.78, 0.79, 0.8, 0.81, 0.8, 0.82, 0.81, 0.82],
      metadata: {},
      diff: 0.01,
    },
    total_requests: {
      name: "Total requests",
      value: 1247,
      history: [980, 1020, 1050, 1100, 1130, 1180, 1210, 1247],
      metadata: {},
      diff: 37,
    },
    consent_rate: {
      name: "Consent rate",
      value: 0.68,
      history: [0.74, 0.73, 0.72, 0.71, 0.7, 0.69, 0.68, 0.68],
      metadata: {},
      diff: -0.02,
    },
  },
};

export const mockAstralis: AstralisResponse = {
  active_conversations: 3,
  completed_assessments: 12,
  awaiting_response: 4,
  risks_identified: 7,
};

const hoursAgo = (h: number) =>
  new Date(Date.now() - h * 3_600_000).toISOString();

export const mockActivityFeedItems: ActivityFeedItem[] = [
  {
    actor_type: "agent",
    message: "completed PIA for the new Marketing Analytics platform",
    timestamp: hoursAgo(0.5),
  },
  {
    actor_type: "user",
    message: "approved data mapping for CRM system",
    timestamp: hoursAgo(1),
  },
  {
    actor_type: "agent",
    message: "flagged consent anomaly in EU region — opt-in rate dropped 12%",
    timestamp: hoursAgo(2),
  },
  {
    actor_type: "user",
    message: "resolved DSR #4821 (erasure request)",
    timestamp: hoursAgo(3),
  },
  {
    actor_type: "agent",
    message: "auto-classified 38 new data fields in Warehouse schema",
    timestamp: hoursAgo(5),
  },
  {
    actor_type: "user",
    message: "updated retention policy for HR records",
    timestamp: hoursAgo(8),
  },
  {
    actor_type: "agent",
    message: "identified 3 systems sharing data without a legal basis",
    timestamp: hoursAgo(14),
  },
  {
    actor_type: "user",
    message: "assigned steward role to J. Martinez for Finance dept",
    timestamp: hoursAgo(22),
  },
  {
    actor_type: "agent",
    message: "generated monthly compliance summary report",
    timestamp: hoursAgo(36),
  },
  {
    actor_type: "user",
    message: "added new vendor Snowflake to system registry",
    timestamp: hoursAgo(48),
  },
];
