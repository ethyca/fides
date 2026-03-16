import { baseApi } from "~/features/common/api.slice";

import type {
  ActivityFeedParams,
  ActivityFeedResponse,
  AgentBriefingResponse,
  AstralisResponse,
  PostureResponse,
  PriorityAction,
  PriorityActionsParams,
  PriorityActionsResponse,
  PrivacyRequestsParams,
  PrivacyRequestsResponse,
  ResetResponse,
  TrendsResponse,
} from "./types";
import { TrendPeriod } from "./types";

const dashboardApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    resetDashboard: build.mutation<ResetResponse, void>({
      query: () => ({ url: "plus/dashboard/reset", method: "POST" }),
      invalidatesTags: ["Fides Dashboard"],
    }),
    getDashboardPosture: build.query<PostureResponse, void>({
      query: () => ({ url: "plus/dashboard/posture" }),
      providesTags: [{ type: "Fides Dashboard", id: "posture" }],
    }),
    getAgentBriefing: build.query<AgentBriefingResponse, void>({
      query: () => ({ url: "plus/dashboard/agent-briefing" }),
      providesTags: [{ type: "Fides Dashboard", id: "briefing" }],
    }),
    getPriorityActions: build.query<
      PriorityActionsResponse,
      PriorityActionsParams | void
    >({
      query: (params) => {
        const { dimension, ...rest } = params ?? {};
        return {
          url: "plus/dashboard/actions",
          params: {
            page: 1,
            size: 25,
            ...rest,
            ...(dimension ? { dimension } : {}),
          },
        };
      },
      providesTags: [{ type: "Fides Dashboard", id: "actions" }],
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
      invalidatesTags: [{ type: "Fides Dashboard", id: "actions" }],
    }),
    getDashboardTrends: build.query<TrendsResponse, { period: TrendPeriod }>({
      query: (params) => ({
        url: "plus/dashboard/trends",
        params,
      }),
      providesTags: [{ type: "Fides Dashboard", id: "trends" }],
    }),
    getAstralis: build.query<AstralisResponse, void>({
      query: () => ({ url: "plus/dashboard/astralis" }),
      providesTags: [{ type: "Fides Dashboard", id: "astralis" }],
    }),
    getActivityFeed: build.query<
      ActivityFeedResponse,
      ActivityFeedParams | void
    >({
      query: (params) => ({
        url: "plus/dashboard/activity-feed",
        params: params ?? {},
      }),
      providesTags: [{ type: "Fides Dashboard", id: "activity-feed" }],
    }),
    getPrivacyRequests: build.query<
      PrivacyRequestsResponse,
      PrivacyRequestsParams | void
    >({
      query: (params) => ({
        url: "plus/dashboard/privacy-requests",
        params: params ?? {},
      }),
      providesTags: [{ type: "Fides Dashboard", id: "privacy-requests" }],
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
