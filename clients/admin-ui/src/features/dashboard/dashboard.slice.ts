import { baseApi } from "~/features/common/api.slice";

// --- Shared types ---

type PostureBand = "critical" | "at_risk" | "good" | "excellent";
type DiffDirection = "up" | "down" | "unchanged";

export interface PostureDimension {
  dimension: string;
  label: string;
  weight: number;
  score: number;
  band: PostureBand;
}

export interface PostureResponse {
  score: number;
  diff: number;
  diff_direction: DiffDirection;
  agent_annotation: string;
  dimensions: PostureDimension[];
}

// --- Agent Briefing ---

interface QuickAction {
  id: string;
  title: string;
  action: string;
  action_url: string;
}

interface AgentBriefingResponse {
  briefing: string;
  quick_actions: QuickAction[];
}

// --- Priority Actions ---

type ActionType =
  | "classification_review"
  | "dsr_action"
  | "system_review"
  | "steward_assignment"
  | "consent_anomaly"
  | "policy_violation"
  | "pia_update";

type ActionStatus = "pending" | "in_progress" | "completed";

export interface PriorityAction {
  id: string;
  priority: number;
  title: string;
  message: string;
  agent_summary: string;
  due_date: string | null;
  action: ActionType;
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
}

// --- Trends ---

type TrendPeriod = "30d" | "60d" | "90d";

export interface TrendMetric {
  value: number;
  history: number[];
  metadata: Record<string, unknown>;
  diff: number;
}

interface TrendsResponse {
  metrics: TrendMetric[];
}

// --- Astralis ---

interface AstralisResponse {
  active_conversations: number;
  completed_assessments: number;
  awaiting_response: number;
  risks_identified: number;
}

// --- Activity Feed ---

interface ActivityFeedItem {
  actor_type: "user" | "agent";
  message: string;
  timestamp: string;
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
}

// --- Privacy Requests ---

interface PrivacyRequestRegion {
  name: string;
  level: "global" | "country" | "state";
  access_count: number;
  erasure_count: number;
}

interface PrivacyRequestsResponse {
  diff_month_over_month: number;
  regions: PrivacyRequestRegion[];
}

interface PrivacyRequestsParams {
  country?: string;
}

// --- Reset ---

interface ResetResponse {
  message: string;
}

// --- API ---

const dashboardApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    resetDashboard: build.mutation<ResetResponse, void>({
      query: () => ({ url: "plus/dashboard/reset", method: "POST" }),
      invalidatesTags: ["Dashboard"],
    }),
    getDashboardPosture: build.query<PostureResponse, void>({
      query: () => ({ url: "plus/dashboard/posture" }),
      providesTags: ["Dashboard"],
    }),
    getAgentBriefing: build.query<AgentBriefingResponse, void>({
      query: () => ({ url: "plus/dashboard/agent-briefing" }),
      providesTags: ["Dashboard"],
    }),
    getPriorityActions: build.query<
      PriorityActionsResponse,
      PriorityActionsParams | void
    >({
      query: (params) => ({
        url: "plus/dashboard/actions",
        params: params ?? { page: 1, size: 8 },
      }),
      providesTags: ["Dashboard"],
    }),
    updatePriorityAction: build.mutation<
      PriorityAction,
      { actionId: string; body: Partial<PriorityAction> }
    >({
      query: ({ actionId, body }) => ({
        url: `plus/dashboard/actions/${actionId}`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["Dashboard"],
    }),
    getDashboardTrends: build.query<TrendsResponse, { period: TrendPeriod }>({
      query: (params) => ({
        url: "plus/dashboard/trends",
        params,
      }),
      providesTags: ["Dashboard"],
    }),
    getAstralis: build.query<AstralisResponse, void>({
      query: () => ({ url: "plus/dashboard/astralis" }),
      providesTags: ["Dashboard"],
    }),
    getActivityFeed: build.query<
      ActivityFeedResponse,
      ActivityFeedParams | void
    >({
      query: (params) => ({
        url: "plus/dashboard/activity-feed",
        params: params ?? {},
      }),
      providesTags: ["Dashboard"],
    }),
    getPrivacyRequests: build.query<
      PrivacyRequestsResponse,
      PrivacyRequestsParams | void
    >({
      query: (params) => ({
        url: "plus/dashboard/privacy-requests",
        params: params ?? {},
      }),
      providesTags: ["Dashboard"],
    }),
  }),
});

export const {
  useResetDashboardMutation,
  useGetDashboardPostureQuery,
  useGetAgentBriefingQuery,
  useGetPriorityActionsQuery,
  useUpdatePriorityActionMutation,
  useGetDashboardTrendsQuery,
  useGetAstralisQuery,
  useGetActivityFeedQuery,
  useGetPrivacyRequestsQuery,
} = dashboardApi;
