export enum PostureBand {
  CRITICAL = "critical",
  AT_RISK = "at_risk",
  GOOD = "good",
  EXCELLENT = "excellent",
}

export enum DiffDirection {
  UP = "up",
  DOWN = "down",
  UNCHANGED = "unchanged",
}

export interface PostureDimension {
  dimension: string;
  label: string;
  weight: number;
  score: number;
  band: PostureBand;
}

export interface PostureResponse {
  score: number;
  band: PostureBand;
  diff_percent: number;
  diff_direction: DiffDirection;
  agent_annotation: string;
  dimensions: PostureDimension[];
}

export enum ActionType {
  CLASSIFICATION_REVIEW = "classification_review",
  DSR_ACTION = "dsr_action",
  SYSTEM_REVIEW = "system_review",
  STEWARD_ASSIGNMENT = "steward_assignment",
  CONSENT_ANOMALY = "consent_anomaly",
  POLICY_VIOLATION = "policy_violation",
  PIA_UPDATE = "pia_update",
}

export enum ActionSeverity {
  CRITICAL = "critical",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
}

export enum ActionStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
}

export interface PriorityAction {
  id: string;
  type: ActionType;
  severity: ActionSeverity;
  title: string;
  message: string;
  agent_summary: string;
  due_date: string | null;
  action_data: Record<string, unknown>;
  status: ActionStatus;
}

interface PriorityActionsResponse {
  items: PriorityAction[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface PriorityActionsParams {
  page?: number;
  size?: number;
  dimension?: string | null;
}

export type { PriorityActionsParams, PriorityActionsResponse };

export enum TrendPeriod {
  THIRTY_DAYS = "30d",
  SIXTY_DAYS = "60d",
  NINETY_DAYS = "90d",
}

export interface TrendMetric {
  value: number;
  history: number[];
  metadata: Record<string, unknown>;
  diff: number;
  agent_summary?: string;
}

interface TrendsResponse {
  metrics: Record<string, TrendMetric>;
}

export type { TrendsResponse };

export interface AstralisResponse {
  active_conversations: number;
  completed_assessments: number;
  awaiting_response: number;
  risks_identified: number;
}

export interface ActivityFeedItem {
  id: string;
  actor_type: "user" | "system";
  message: string;
  timestamp: string;
  event_source?: "helios" | "janus" | "lethe" | "astralis";
  event_type?: ActionType;
  action_data?: Record<string, unknown>;
}

interface ActivityFeedResponse {
  items: ActivityFeedItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface ActivityFeedParams {
  page?: number;
  size?: number;
  start_date?: string;
  end_date?: string;
  actor_type?: "user" | "system";
}

export type { ActivityFeedParams, ActivityFeedResponse };

interface PrivacyRequestsResponse {
  active_count: number;
  statuses: {
    in_progress: number;
    pending_action: number;
    awaiting_approval: number;
  };
  overdue_count: number;
  sla_health: Record<
    string,
    { on_track: number; approaching: number; overdue: number }
  >;
  agent_summary?: string;
}

export type { PrivacyRequestsResponse };

export interface QuickAction {
  label: string;
  action_type: ActionType;
  action_data: Record<string, unknown>;
  severity: ActionSeverity;
}

interface AgentBriefingResponse {
  briefing: string;
  quick_actions: QuickAction[];
}

export type { AgentBriefingResponse };

interface ResetResponse {
  message: string;
}

export type { ResetResponse };

export interface SystemCoverageResponse {
  total_systems: number;
  fully_classified: number;
  partially_classified: number;
  unclassified: number;
  without_steward: number;
  coverage_percentage: number;
  agent_summary?: string;
}
