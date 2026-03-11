const now = new Date();
const hoursAgo = (h: number) =>
  new Date(now.getTime() - h * 3600_000).toISOString();

export const MOCK_ACTIVITY_FEED = {
  items: [
    {
      actor_type: "agent" as const,
      message: "completed PIA for the new Marketing Analytics platform",
      timestamp: hoursAgo(0.5),
    },
    {
      actor_type: "user" as const,
      message: "approved data mapping for CRM system",
      timestamp: hoursAgo(1),
    },
    {
      actor_type: "agent" as const,
      message: "flagged consent anomaly in EU region — opt-in rate dropped 12%",
      timestamp: hoursAgo(2),
    },
    {
      actor_type: "user" as const,
      message: "resolved DSR #4821 (erasure request)",
      timestamp: hoursAgo(3),
    },
    {
      actor_type: "agent" as const,
      message: "auto-classified 38 new data fields in Warehouse schema",
      timestamp: hoursAgo(5),
    },
    {
      actor_type: "user" as const,
      message: "updated retention policy for HR records",
      timestamp: hoursAgo(8),
    },
    {
      actor_type: "agent" as const,
      message: "identified 3 systems sharing data without a legal basis",
      timestamp: hoursAgo(14),
    },
    {
      actor_type: "user" as const,
      message: "assigned steward role to J. Martinez for Finance dept",
      timestamp: hoursAgo(22),
    },
    {
      actor_type: "agent" as const,
      message: "generated monthly compliance summary report",
      timestamp: hoursAgo(36),
    },
    {
      actor_type: "user" as const,
      message: "added new vendor Snowflake to system registry",
      timestamp: hoursAgo(48),
    },
  ],
  total: 10,
  page: 1,
  size: 10,
  pages: 1,
};

export const MOCK_PRIORITY_ACTIONS = {
  items: [
    {
      id: "pa-1",
      priority: 1,
      title: "Review classification changes",
      message:
        "38 fields auto-classified in Warehouse — 4 flagged as sensitive",
      agent_summary: "",
      due_date: hoursAgo(-24),
      action: "classification_review" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-2",
      priority: 2,
      title: "Consent anomaly in EU",
      message: "Opt-in rate for cookie consent dropped 12% week-over-week",
      agent_summary: "",
      due_date: hoursAgo(-48),
      action: "consent_anomaly" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-3",
      priority: 3,
      title: "DSR escalation — erasure #4910",
      message: "Erasure request approaching SLA deadline (2 days remaining)",
      agent_summary: "",
      due_date: hoursAgo(-36),
      action: "dsr_action" as const,
      action_data: {},
      status: "in_progress" as const,
    },
    {
      id: "pa-4",
      priority: 4,
      title: "Policy violation detected",
      message:
        "Marketing system sharing email data with 3rd party without legal basis",
      agent_summary: "",
      due_date: hoursAgo(-12),
      action: "policy_violation" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-5",
      priority: 5,
      title: "Assign steward for new Analytics dept",
      message: "New department created with 12 systems — no steward assigned",
      agent_summary: "",
      due_date: null,
      action: "steward_assignment" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-6",
      priority: 6,
      title: "PIA update needed for Payment Gateway",
      message: "System configuration changed since last assessment 90 days ago",
      agent_summary: "",
      due_date: null,
      action: "pia_update" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-7",
      priority: 7,
      title: "System review — new vendor Snowflake",
      message: "Newly registered system needs data flow and risk review",
      agent_summary: "",
      due_date: null,
      action: "system_review" as const,
      action_data: {},
      status: "pending" as const,
    },
    {
      id: "pa-8",
      priority: 8,
      title: "Review DSR automation rules",
      message:
        "Agent suggests updating auto-approval rules based on recent patterns",
      agent_summary: "",
      due_date: null,
      action: "dsr_action" as const,
      action_data: {},
      status: "pending" as const,
    },
  ],
  total: 8,
  page: 1,
  size: 8,
  pages: 1,
};
